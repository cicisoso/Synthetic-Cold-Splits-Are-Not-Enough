from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score


def _safe_topn(length: int, frac: float) -> int:
    return max(1, int(np.ceil(length * frac)))


def global_enrichment(labels: np.ndarray, probabilities: np.ndarray, top_fracs: Iterable[float]) -> dict[str, float]:
    labels = np.asarray(labels, dtype=np.int64)
    probabilities = np.asarray(probabilities, dtype=np.float32)
    order = np.argsort(-probabilities)
    base_rate = float(labels.mean())
    payload = {"base_positive_rate": base_rate}
    for frac in top_fracs:
        topn = _safe_topn(len(labels), frac)
        top_rate = float(labels[order[:topn]].mean())
        gain = top_rate / max(base_rate, 1e-12)
        key = f"ef_at_{int(round(frac * 100))}pct"
        payload[key] = float(gain)
        payload[f"top_rate_at_{int(round(frac * 100))}pct"] = top_rate
    return payload


def per_group_decision_metrics(
    frame: pd.DataFrame,
    group_col: str,
    label_col: str,
    prob_col: str,
    ks: Iterable[int],
) -> dict:
    metrics = {
        "num_groups": int(frame[group_col].nunique()),
        "groups_with_positive": 0,
        "macro_auprc": None,
        "hit_rate": {},
        "precision": {},
        "recall": {},
    }
    ap_values = []
    hit_values = {int(k): [] for k in ks}
    precision_values = {int(k): [] for k in ks}
    recall_values = {int(k): [] for k in ks}

    for _, group in frame.groupby(group_col):
        labels = group[label_col].to_numpy(dtype=np.int64)
        probs = group[prob_col].to_numpy(dtype=np.float32)
        if labels.sum() <= 0:
            continue
        metrics["groups_with_positive"] += 1
        order = np.argsort(-probs)
        sorted_labels = labels[order]
        positives = int(sorted_labels.sum())
        if len(np.unique(labels)) > 1:
            ap_values.append(float(average_precision_score(labels, probs)))
        for k in ks:
            topk = min(int(k), len(sorted_labels))
            hits = int(sorted_labels[:topk].sum())
            hit_values[int(k)].append(float(hits > 0))
            precision_values[int(k)].append(float(hits / max(topk, 1)))
            recall_values[int(k)].append(float(hits / max(positives, 1)))

    metrics["macro_auprc"] = float(np.mean(ap_values)) if ap_values else None
    for k in ks:
        key = str(int(k))
        metrics["hit_rate"][key] = float(np.mean(hit_values[int(k)])) if hit_values[int(k)] else None
        metrics["precision"][key] = float(np.mean(precision_values[int(k)])) if precision_values[int(k)] else None
        metrics["recall"][key] = float(np.mean(recall_values[int(k)])) if recall_values[int(k)] else None
    return metrics


def merged_decision_metrics(
    merged: pd.DataFrame,
    group_col: str = "Target_ID",
    label_col: str = "label",
    prob_col: str = "probability",
    ks: Iterable[int] = (1, 3, 5, 10, 20),
    top_fracs: Iterable[float] = (0.01, 0.05, 0.10),
) -> dict:
    labels = merged[label_col].to_numpy(dtype=np.int64)
    probabilities = merged[prob_col].to_numpy(dtype=np.float32)
    payload = {
        "global_enrichment": global_enrichment(labels, probabilities, top_fracs),
        "per_target": per_group_decision_metrics(
            frame=merged,
            group_col=group_col,
            label_col=label_col,
            prob_col=prob_col,
            ks=ks,
        ),
    }
    return payload
