from __future__ import annotations

import math
from typing import Dict, List

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    f1_score,
    roc_auc_score,
)


def expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    total = len(y_true)
    ece = 0.0
    for i in range(n_bins):
        mask = (y_prob >= bins[i]) & (y_prob < bins[i + 1] if i < n_bins - 1 else y_prob <= bins[i + 1])
        if not np.any(mask):
            continue
        acc = float(np.mean(y_true[mask]))
        conf = float(np.mean(y_prob[mask]))
        ece += abs(acc - conf) * (np.sum(mask) / total)
    return float(ece)


def binary_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob).astype(float)
    y_pred = (y_prob >= 0.5).astype(int)

    metrics = {
        "auprc": float(average_precision_score(y_true, y_prob)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "brier": float(brier_score_loss(y_true, y_prob)),
        "ece": float(expected_calibration_error(y_true, y_prob)),
        "positive_rate": float(np.mean(y_true)),
    }
    if len(np.unique(y_true)) > 1:
        metrics["auroc"] = float(roc_auc_score(y_true, y_prob))
    else:
        metrics["auroc"] = math.nan
    return metrics


def stratified_overlap_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    overlap_score: np.ndarray,
    num_buckets: int = 3,
) -> List[Dict[str, float]]:
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    overlap_score = np.asarray(overlap_score)
    quantiles = np.linspace(0, 1, num_buckets + 1)
    boundaries = np.quantile(overlap_score, quantiles)
    results = []
    for idx in range(num_buckets):
        low = boundaries[idx]
        high = boundaries[idx + 1]
        if idx == num_buckets - 1:
            mask = (overlap_score >= low) & (overlap_score <= high)
        else:
            mask = (overlap_score >= low) & (overlap_score < high)
        if np.sum(mask) < 8 or len(np.unique(y_true[mask])) < 2:
            results.append(
                {
                    "bucket": idx,
                    "low": float(low),
                    "high": float(high),
                    "count": int(np.sum(mask)),
                }
            )
            continue
        entry = binary_metrics(y_true[mask], y_prob[mask])
        entry.update(
            {
                "bucket": idx,
                "low": float(low),
                "high": float(high),
                "count": int(np.sum(mask)),
            }
        )
        results.append(entry)
    return results
