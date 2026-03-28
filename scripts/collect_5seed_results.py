#!/usr/bin/env python3
"""Collect 5-seed results from the 5seed_* directories and print formatted tables."""
import json
import statistics
from pathlib import Path

MODELS = ["base", "rf", "dtilm", "hyperpcm", "graphdta", "drugban", "coldstartcpi"]
BENCHMARKS = {
    "unseen_drug": ("BindingDB_Kd", "unseen_drug"),
    "blind_start": ("BindingDB_Kd", "blind_start"),
    "unseen_target": ("BindingDB_Kd", "unseen_target"),
    "patent": ("BindingDB_patent", "patent_temporal"),
    "nonpatent": ("BindingDB_nonpatent_Kd", "nonpatent_temporal"),
}

results_dir = Path("results")

def find_result(model, benchmark_key, seed):
    dataset, split = BENCHMARKS[benchmark_key]
    dirname = f"5seed_{model}_{benchmark_key}"
    if benchmark_key == "patent":
        dirname = f"5seed_{model}_patent"
    elif benchmark_key == "nonpatent":
        dirname = f"5seed_{model}_nonpatent"
    filename = f"{dataset}_{split}_{model}_seed{seed}.json"
    path = results_dir / dirname / filename
    if path.exists():
        with open(path) as f:
            data = json.load(f)
        return data["test_metrics"]["auprc"], data["test_metrics"]["auroc"]
    return None, None

print("=" * 120)
print("  5-SEED RESULTS COLLECTION")
print("=" * 120)

for bk in BENCHMARKS:
    print(f"\n### {bk}")
    print(f"{'Model':<16} {'Seeds':>5} {'AUPRC (mean±std)':>22} {'AUROC (mean±std)':>22} {'Per-seed AUPRC':>50}")
    print("-" * 120)
    for model in MODELS:
        auprcs, aurocs = [], []
        for seed in range(5):
            auprc, auroc = find_result(model, bk, seed)
            if auprc is not None:
                auprcs.append(auprc)
                aurocs.append(auroc)
        if auprcs:
            mean_auprc = statistics.mean(auprcs)
            std_auprc = statistics.pstdev(auprcs)
            mean_auroc = statistics.mean(aurocs)
            std_auroc = statistics.pstdev(aurocs)
            seeds_str = ", ".join(f"{x:.4f}" for x in auprcs)
            print(f"{model:<16} {len(auprcs):>5} {mean_auprc:>8.4f} ± {std_auprc:.4f}  {mean_auroc:>8.4f} ± {std_auroc:.4f}  [{seeds_str}]")
        else:
            print(f"{model:<16}     0  --- no results ---")

# LaTeX table snippet
print("\n" + "=" * 120)
print("  LATEX TABLE SNIPPET (for main.tex)")
print("=" * 120)
for model in MODELS:
    cells = []
    for bk in BENCHMARKS:
        auprcs, aurocs = [], []
        for seed in range(5):
            auprc, auroc = find_result(model, bk, seed)
            if auprc is not None:
                auprcs.append(auprc)
                aurocs.append(auroc)
        if len(auprcs) >= 3:
            mean_auprc = statistics.mean(auprcs)
            std_auprc = statistics.pstdev(auprcs)
            mean_auroc = statistics.mean(aurocs)
            std_auroc = statistics.pstdev(aurocs)
            cells.append(f"{mean_auprc:.4f} $\\pm$ {std_auprc:.4f}\\\\{mean_auroc:.4f} $\\pm$ {std_auroc:.4f}")
        else:
            cells.append("--- \\\\ ---")
    print(f"    \\texttt{{{model}}} &")
    for i, cell in enumerate(cells):
        sep = " \\\\" if i == len(cells) - 1 else " &"
        print(f"    \\shortstack[c]{{{cell}}}{sep}")
