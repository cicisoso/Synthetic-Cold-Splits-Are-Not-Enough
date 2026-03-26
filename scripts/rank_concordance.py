#!/usr/bin/env python3
"""Compute Kendall's W and Spearman rank correlations for DTI benchmark ranking stability."""

import numpy as np
from itertools import combinations
from scipy.stats import rankdata, spearmanr, chi2


def kendall_w(ranks_matrix):
    """Compute Kendall's W (coefficient of concordance).

    Parameters
    ----------
    ranks_matrix : np.ndarray, shape (k, n)
        k raters (benchmarks) each ranking n objects (models).

    Returns
    -------
    W : float
    chi2_stat : float
    p_value : float
    """
    k, n = ranks_matrix.shape
    # Sum of ranks for each object across all raters
    R = ranks_matrix.sum(axis=0)
    R_bar = R.mean()
    S = np.sum((R - R_bar) ** 2)
    W = 12.0 * S / (k ** 2 * (n ** 3 - n))
    chi2_stat = k * (n - 1) * W
    p_value = 1.0 - chi2.cdf(chi2_stat, df=n - 1)
    return W, chi2_stat, p_value


def run_analysis(metric_name, models, benchmarks, data):
    """Run the full concordance analysis for one metric.

    Parameters
    ----------
    metric_name : str
    models : list of str
    benchmarks : list of str
    data : np.ndarray, shape (n_models, n_benchmarks)
    """
    n_models, n_benchmarks = data.shape

    print("=" * 80)
    print(f"  RANKING CONCORDANCE ANALYSIS  --  {metric_name}")
    print("=" * 80)

    # ---- Raw scores table ----
    print(f"\n{'Model':<12}", end="")
    for b in benchmarks:
        print(f"{b:>20}", end="")
    print()
    print("-" * (12 + 20 * n_benchmarks))
    for i, m in enumerate(models):
        print(f"{m:<12}", end="")
        for j in range(n_benchmarks):
            print(f"{data[i, j]:>20.4f}", end="")
        print()

    # ---- Ranks (1 = best = highest score) ----
    # rankdata gives rank 1 to smallest; we want 1 = largest, so negate
    ranks = np.zeros_like(data, dtype=float)
    for j in range(n_benchmarks):
        ranks[:, j] = rankdata(-data[:, j], method="average")

    print(f"\n{'Model':<12}", end="")
    for b in benchmarks:
        print(f"{b:>20}", end="")
    print(f"{'Mean Rank':>12}")
    print("-" * (12 + 20 * n_benchmarks + 12))
    for i, m in enumerate(models):
        print(f"{m:<12}", end="")
        for j in range(n_benchmarks):
            print(f"{ranks[i, j]:>20.1f}", end="")
        print(f"{ranks[i, :].mean():>12.2f}")

    # ---- Kendall's W: all benchmarks ----
    # ranks_matrix shape: (k_raters=benchmarks, n_objects=models) => transpose
    ranks_T = ranks.T  # shape (n_benchmarks, n_models)

    W_all, chi2_all, p_all = kendall_w(ranks_T)
    print(f"\n--- Kendall's W (all {n_benchmarks} benchmarks) ---")
    print(f"  W = {W_all:.4f}   chi2({n_models - 1}) = {chi2_all:.3f}   p = {p_all:.4f}")

    # ---- Kendall's W: synthetic only (first 3) ----
    if n_benchmarks >= 3:
        W_syn, chi2_syn, p_syn = kendall_w(ranks_T[:3, :])
        print(f"\n--- Kendall's W (synthetic: {', '.join(benchmarks[:3])}) ---")
        print(f"  W = {W_syn:.4f}   chi2({n_models - 1}) = {chi2_syn:.3f}   p = {p_syn:.4f}")

    # ---- Kendall's W: temporal only (last 2) ----
    if n_benchmarks >= 5:
        W_tmp, chi2_tmp, p_tmp = kendall_w(ranks_T[3:5, :])
        print(f"\n--- Kendall's W (temporal: {', '.join(benchmarks[3:5])}) ---")
        print(f"  W = {W_tmp:.4f}   chi2({n_models - 1}) = {chi2_tmp:.3f}   p = {p_tmp:.4f}")

    # ---- Spearman rank correlation between every pair of benchmarks ----
    print(f"\n--- Spearman rank correlations (pairwise benchmarks) ---")
    # Header
    print(f"{'':>20}", end="")
    for b in benchmarks:
        print(f"{b:>20}", end="")
    print()

    rho_matrix = np.ones((n_benchmarks, n_benchmarks))
    p_matrix = np.zeros((n_benchmarks, n_benchmarks))
    for i in range(n_benchmarks):
        for j in range(n_benchmarks):
            if i != j:
                rho, p = spearmanr(ranks[:, i], ranks[:, j])
                rho_matrix[i, j] = rho
                p_matrix[i, j] = p

    for i, bi in enumerate(benchmarks):
        print(f"{bi:>20}", end="")
        for j in range(n_benchmarks):
            if i == j:
                print(f"{'1.000':>20}", end="")
            else:
                star = "*" if p_matrix[i, j] < 0.05 else ""
                print(f"{rho_matrix[i, j]:>18.3f}{star:>2}", end="")
        print()

    print("\n  (* = p < 0.05)")

    # ---- Summary: mean rho within and across groups ----
    syn_idx = list(range(3))
    tmp_idx = list(range(3, min(5, n_benchmarks)))

    rhos_within_syn = [rho_matrix[i, j] for i, j in combinations(syn_idx, 2)]
    rhos_within_tmp = [rho_matrix[i, j] for i, j in combinations(tmp_idx, 2)]
    rhos_cross = [rho_matrix[i, j] for i in syn_idx for j in tmp_idx]

    print(f"\n--- Average Spearman rho by group ---")
    if rhos_within_syn:
        print(f"  Within synthetic  (n={len(rhos_within_syn)} pairs): "
              f"mean rho = {np.mean(rhos_within_syn):.3f}")
    if rhos_within_tmp:
        print(f"  Within temporal   (n={len(rhos_within_tmp)} pairs): "
              f"mean rho = {np.mean(rhos_within_tmp):.3f}")
    if rhos_cross:
        print(f"  Cross-group       (n={len(rhos_cross)} pairs): "
              f"mean rho = {np.mean(rhos_cross):.3f}")

    print()
    return W_all


# ============================================================
# Data
# ============================================================
models = ["base", "RF", "DTI-LM", "HyperPCM", "GraphDTA", "DrugBAN"]
benchmarks = ["unseen_drug", "blind_start", "unseen_target",
              "patent_temporal", "nonpatent_temporal"]

auprc = np.array([
    [0.5509, 0.3737, 0.5224, 0.7772, 0.6369],
    [0.7339, 0.4512, 0.5183, 0.8234, 0.7201],
    [0.5004, 0.3636, 0.5136, 0.7825, 0.6531],
    [0.5694, 0.3828, 0.4955, 0.7753, 0.6287],
    [0.5626, 0.3910, 0.4722, 0.7726, 0.6635],
    [0.5856, 0.4111, 0.4219, 0.7548, 0.6289],
])

auroc = np.array([
    [0.7794, 0.6778, 0.7741, 0.7223, 0.7333],
    [0.8854, 0.7451, 0.7838, 0.7773, 0.7627],
    [0.7364, 0.6490, 0.7970, 0.7362, 0.7644],
    [0.7778, 0.6807, 0.7810, 0.7368, 0.7450],
    [0.7988, 0.7141, 0.7637, 0.7232, 0.7334],
    [0.8085, 0.7192, 0.7397, 0.7039, 0.7151],
])

W_auprc = run_analysis("AUPRC", models, benchmarks, auprc)
W_auroc = run_analysis("AUROC", models, benchmarks, auroc)

# ---- Cross-metric comparison ----
print("=" * 80)
print("  CROSS-METRIC SUMMARY")
print("=" * 80)
print(f"\n  Kendall's W (all 5 benchmarks):")
print(f"    AUPRC: {W_auprc:.4f}")
print(f"    AUROC: {W_auroc:.4f}")
print(f"\n  Interpretation guide:")
print(f"    W < 0.3  => weak agreement   (rankings differ substantially)")
print(f"    0.3-0.5  => moderate          (some consistency)")
print(f"    0.5-0.7  => good              (fair consistency)")
print(f"    0.7-1.0  => strong/perfect    (highly consistent rankings)")
print()
