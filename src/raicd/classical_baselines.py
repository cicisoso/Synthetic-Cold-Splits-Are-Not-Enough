from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from .featurizers import sequence_to_hashed_kmers, smiles_to_morgan
from .metrics import binary_metrics, stratified_overlap_metrics


EntityFeaturizer = Callable[[str], np.ndarray]


@dataclass
class EntityFeatureTable:
    ids: list[str]
    features: np.ndarray

    @property
    def lookup(self) -> dict[str, int]:
        return {entity_id: idx for idx, entity_id in enumerate(self.ids)}


def _load_feature_cache(cache_path: Path) -> EntityFeatureTable | None:
    if not cache_path.exists():
        return None
    payload = np.load(cache_path, allow_pickle=False)
    ids = payload["ids"].astype(str).tolist()
    features = payload["features"].astype(np.float32)
    return EntityFeatureTable(ids=ids, features=features)


def _save_feature_cache(cache_path: Path, table: EntityFeatureTable) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        cache_path,
        ids=np.asarray(table.ids, dtype="<U128"),
        features=table.features.astype(np.float32),
    )


def load_or_compute_entity_features(
    frame: pd.DataFrame,
    id_col: str,
    text_col: str,
    featurizer: EntityFeaturizer,
    cache_path: Path,
) -> EntityFeatureTable:
    expected_ids = frame[id_col].astype(str).tolist()
    cached = _load_feature_cache(cache_path)
    if cached is not None and cached.ids == expected_ids:
        return cached

    features = np.stack([featurizer(str(text)) for text in frame[text_col].astype(str).tolist()]).astype(np.float32)
    table = EntityFeatureTable(ids=expected_ids, features=features)
    _save_feature_cache(cache_path, table)
    return table


def drug_feature_table(
    drugs: pd.DataFrame,
    cache_path: Path,
    n_bits: int = 2048,
    radius: int = 2,
) -> EntityFeatureTable:
    return load_or_compute_entity_features(
        frame=drugs,
        id_col="drug_id",
        text_col="drug_smile",
        featurizer=lambda smiles: smiles_to_morgan(smiles, n_bits=n_bits, radius=radius),
        cache_path=cache_path,
    )


def target_feature_table(
    targets: pd.DataFrame,
    cache_path: Path,
    dim: int = 2048,
) -> EntityFeatureTable:
    return load_or_compute_entity_features(
        frame=targets,
        id_col="prot_id",
        text_col="prot_seq",
        featurizer=lambda seq: sequence_to_hashed_kmers(seq, dim=dim),
        cache_path=cache_path,
    )


def build_pair_matrix(
    frame: pd.DataFrame,
    drug_lookup: dict[str, int],
    target_lookup: dict[str, int],
    drug_features: np.ndarray,
    target_features: np.ndarray,
    pair_feature_mode: str = "concat",
) -> np.ndarray:
    drug_idx = frame["Drug_ID"].astype(str).map(drug_lookup).to_numpy(dtype=np.int64)
    target_idx = frame["Target_ID"].astype(str).map(target_lookup).to_numpy(dtype=np.int64)
    drug_x = drug_features[drug_idx]
    target_x = target_features[target_idx]
    if pair_feature_mode == "concat":
        return np.concatenate([drug_x, target_x], axis=1).astype(np.float32)
    if pair_feature_mode == "concat_absdiff":
        return np.concatenate([drug_x, target_x, np.abs(drug_x - target_x)], axis=1).astype(np.float32)
    raise ValueError(f"Unsupported pair_feature_mode: {pair_feature_mode}")


def evaluate_probabilities(frame: pd.DataFrame, probabilities: np.ndarray) -> tuple[dict, dict]:
    labels = frame["label"].to_numpy(dtype=np.int64)
    overlap = frame["overlap_score"].to_numpy(dtype=np.float32)
    probs = np.asarray(probabilities, dtype=np.float32)
    metrics = binary_metrics(labels, probs)
    metrics["overlap_buckets"] = stratified_overlap_metrics(labels, probs, overlap)
    extras = {
        "example_id": frame["example_id"].astype(str).tolist(),
        "labels": labels.tolist(),
        "probabilities": probs.tolist(),
        "overlap_score": overlap.tolist(),
    }
    return metrics, extras


def save_prediction_csv(path: Path, extras: dict) -> None:
    pd.DataFrame(
        {
            "example_id": extras["example_id"],
            "label": extras["labels"],
            "probability": extras["probabilities"],
            "overlap_score": extras["overlap_score"],
        }
    ).to_csv(path, index=False)


def write_result_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, default=str))
