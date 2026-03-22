from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from transformers import AutoModel, AutoTokenizer


def _sanitize_model_name(model_name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", model_name)


def _stable_ids_hash(ids: list[str]) -> str:
    digest = hashlib.sha1()
    for item in ids:
        digest.update(item.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()[:16]


def _mean_pool(hidden_state: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    mask = attention_mask.unsqueeze(-1).to(hidden_state.dtype)
    masked = hidden_state * mask
    denom = torch.clamp(mask.sum(dim=1), min=1.0)
    return masked.sum(dim=1) / denom


def load_or_compute_pooled_embeddings(
    frame: pd.DataFrame,
    id_col: str,
    text_col: str,
    model_name: str,
    cache_dir: Path,
    device: torch.device,
    batch_size: int = 16,
    max_length: int = 256,
) -> np.ndarray:
    cache_dir.mkdir(parents=True, exist_ok=True)
    ids = frame[id_col].astype(str).tolist()
    ids_hash = _stable_ids_hash(ids)
    cache_tag = f"{text_col}_{_sanitize_model_name(model_name)}_len{max_length}_{ids_hash}"
    cache_path = cache_dir / f"{cache_tag}.npz"
    meta_path = cache_dir / f"{cache_tag}.json"

    if cache_path.exists() and meta_path.exists():
        payload = np.load(cache_path)
        meta = json.loads(meta_path.read_text())
        if meta.get("ids", []) == ids:
            return payload["embeddings"].astype(np.float32)

    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    model = AutoModel.from_pretrained(model_name).to(device)
    model.eval()

    texts = frame[text_col].fillna("").astype(str).tolist()
    pooled_batches = []
    for start in range(0, len(texts), batch_size):
        end = min(start + batch_size, len(texts))
        inputs = tokenizer(
            texts[start:end],
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=max_length,
        )
        inputs = {key: value.to(device) for key, value in inputs.items()}
        with torch.no_grad():
            outputs = model(**inputs)
        pooled = _mean_pool(outputs.last_hidden_state, inputs["attention_mask"])
        pooled_batches.append(pooled.detach().cpu().numpy().astype(np.float32))

    embeddings = np.concatenate(pooled_batches, axis=0).astype(np.float32)
    np.savez_compressed(cache_path, embeddings=embeddings)
    meta_path.write_text(
        json.dumps(
            {
                "model_name": model_name,
                "id_col": id_col,
                "text_col": text_col,
                "max_length": int(max_length),
                "ids": ids,
            },
            indent=2,
        )
    )
    return embeddings
