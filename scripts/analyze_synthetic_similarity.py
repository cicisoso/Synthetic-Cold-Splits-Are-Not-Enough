#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import statistics
import warnings
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from Bio import BiopythonDeprecationWarning
warnings.filterwarnings("ignore", category=BiopythonDeprecationWarning)
from Bio import pairwise2
from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem
from rdkit.Chem.Scaffolds import MurckoScaffold

import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.append(str(SRC))

from raicd.featurizers import sequence_to_hashed_kmers


SPLIT_ENTITY_PLAN = {
    "unseen_drug": ("drug",),
    "unseen_target": ("target",),
    "blind_start": ("drug", "target"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze synthetic split similarity leakage diagnostics.")
    parser.add_argument("--resource-base-dir", type=Path, default=Path("benchmark_resources"))
    parser.add_argument("--dataset", type=str, default="BindingDB_Kd")
    parser.add_argument("--splits", nargs="+", default=["unseen_drug", "unseen_target", "blind_start"])
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    parser.add_argument("--target-shortlist", type=int, default=32)
    parser.add_argument("--kmer-dim", type=int, default=2048)
    parser.add_argument("--output-json", type=Path, default=Path("reports/synthetic_similarity_diagnosis.json"))
    parser.add_argument("--output-md", type=Path, default=Path("reports/SYNTHETIC_SIMILARITY_DIAGNOSIS.md"))
    return parser.parse_args()


def _mean_std(values: list[float]) -> tuple[float, float]:
    if not values:
        return math.nan, math.nan
    if len(values) == 1:
        return float(values[0]), 0.0
    return float(statistics.mean(values)), float(statistics.pstdev(values))


def _fmt_mean_std(values: list[float]) -> str:
    mean, std = _mean_std(values)
    return f"{mean:.4f} ± {std:.4f}"


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return math.nan
    arr = np.asarray(values, dtype=np.float32)
    return float(np.quantile(arr, q))


def _drug_fp(smiles: str, n_bits: int = 2048, radius: int = 2):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)


def _murcko(smiles: str) -> str:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return ""
    return MurckoScaffold.MurckoScaffoldSmiles(mol=mol)


def analyze_drug_split(train_df: pd.DataFrame, test_df: pd.DataFrame) -> dict:
    train_drugs = train_df[["Drug_ID", "Drug"]].drop_duplicates("Drug_ID").reset_index(drop=True)
    test_drugs = test_df[["Drug_ID", "Drug"]].drop_duplicates("Drug_ID").reset_index(drop=True)

    train_fps = []
    train_scaffolds = []
    for smile in train_drugs["Drug"].astype(str).tolist():
        train_fps.append(_drug_fp(smile))
        train_scaffolds.append(_murcko(smile))
    train_scaffold_set = set(scaffold for scaffold in train_scaffolds if scaffold)

    nearest_tanimoto = []
    scaffold_match = []
    for smile in test_drugs["Drug"].astype(str).tolist():
        fp = _drug_fp(smile)
        scaffold = _murcko(smile)
        scaffold_match.append(float(bool(scaffold) and scaffold in train_scaffold_set))
        if fp is None:
            nearest_tanimoto.append(0.0)
            continue
        sims = DataStructs.BulkTanimotoSimilarity(fp, train_fps)
        nearest_tanimoto.append(float(max(sims) if sims else 0.0))

    return {
        "num_train_entities": int(len(train_drugs)),
        "num_test_entities": int(len(test_drugs)),
        "nearest_tanimoto": nearest_tanimoto,
        "scaffold_match": scaffold_match,
        "summary": {
            "mean_tanimoto": float(np.mean(nearest_tanimoto)),
            "median_tanimoto": float(np.median(nearest_tanimoto)),
            "p90_tanimoto": _quantile(nearest_tanimoto, 0.9),
            "frac_tanimoto_ge_0_8": float(np.mean(np.asarray(nearest_tanimoto) >= 0.8)),
            "frac_tanimoto_ge_0_9": float(np.mean(np.asarray(nearest_tanimoto) >= 0.9)),
            "scaffold_match_rate": float(np.mean(scaffold_match)),
        },
    }


def _normalize_rows(x: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(x, axis=1, keepdims=True)
    norm = np.where(norm == 0, 1.0, norm)
    return x / norm


def _pairwise_identity(seq_a: str, seq_b: str) -> float:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        alignment = pairwise2.align.globalms(seq_a, seq_b, 1.0, 0.0, -1.0, -0.1, one_alignment_only=True)[0]
    aligned_a, aligned_b = alignment.seqA, alignment.seqB
    matches = sum(
        a == b
        for a, b in zip(aligned_a, aligned_b)
        if a != "-" and b != "-"
    )
    aligned_len = sum((a != "-" or b != "-") for a, b in zip(aligned_a, aligned_b))
    if aligned_len == 0:
        return 0.0
    return float(matches / aligned_len)


def analyze_target_split(train_df: pd.DataFrame, test_df: pd.DataFrame, shortlist: int, kmer_dim: int) -> dict:
    train_targets = train_df[["Target_ID", "Target"]].drop_duplicates("Target_ID").reset_index(drop=True)
    test_targets = test_df[["Target_ID", "Target"]].drop_duplicates("Target_ID").reset_index(drop=True)

    train_seqs = train_targets["Target"].fillna("").astype(str).tolist()
    test_seqs = test_targets["Target"].fillna("").astype(str).tolist()
    train_feat = _normalize_rows(np.stack([sequence_to_hashed_kmers(seq, dim=kmer_dim) for seq in train_seqs]).astype(np.float32))
    test_feat = _normalize_rows(np.stack([sequence_to_hashed_kmers(seq, dim=kmer_dim) for seq in test_seqs]).astype(np.float32))
    sim = test_feat @ train_feat.T

    nearest_identity = []
    for row_idx, seq in enumerate(test_seqs):
        candidate_idx = np.argsort(sim[row_idx])[-shortlist:]
        best = 0.0
        for idx in candidate_idx:
            ident = _pairwise_identity(seq, train_seqs[int(idx)])
            if ident > best:
                best = ident
        nearest_identity.append(best)

    arr = np.asarray(nearest_identity)
    return {
        "num_train_entities": int(len(train_targets)),
        "num_test_entities": int(len(test_targets)),
        "nearest_identity": nearest_identity,
        "summary": {
            "mean_identity": float(np.mean(arr)),
            "median_identity": float(np.median(arr)),
            "p90_identity": _quantile(nearest_identity, 0.9),
            "frac_identity_ge_0_4": float(np.mean(arr >= 0.4)),
            "frac_identity_ge_0_6": float(np.mean(arr >= 0.6)),
            "frac_identity_ge_0_8": float(np.mean(arr >= 0.8)),
        },
    }


def aggregate_seed_stats(seed_records: list[dict], entity_type: str) -> dict:
    if entity_type == "drug":
        keys = [
            "mean_tanimoto",
            "median_tanimoto",
            "p90_tanimoto",
            "frac_tanimoto_ge_0_8",
            "frac_tanimoto_ge_0_9",
            "scaffold_match_rate",
        ]
    else:
        keys = [
            "mean_identity",
            "median_identity",
            "p90_identity",
            "frac_identity_ge_0_4",
            "frac_identity_ge_0_6",
            "frac_identity_ge_0_8",
        ]
    out = {}
    for key in keys:
        values = [record["summary"][key] for record in seed_records]
        out[key] = {"mean": _mean_std(values)[0], "std": _mean_std(values)[1]}
    return out


def build_markdown(results: dict) -> str:
    lines = [
        "# Synthetic Similarity Diagnosis",
        "",
        "Nearest-neighbor similarity diagnostics for the synthetic `BindingDB_Kd` reference panel.",
        "Drug-cold splits use exact Morgan-fingerprint Tanimoto and Bemis-Murcko scaffold overlap.",
        "Target-cold splits use nearest global sequence identity after a hashed-kmer shortlist.",
        "",
    ]
    for split, payload in results.items():
        lines.append(f"## `{split}`")
        lines.append("")
        for entity_type in payload["entities"]:
            agg = payload["entities"][entity_type]["aggregate"]
            if entity_type == "drug":
                lines.append(
                    f"- Drug nearest Tanimoto: `{agg['median_tanimoto']['mean']:.4f} ± {agg['median_tanimoto']['std']:.4f}` median, "
                    f"`{agg['p90_tanimoto']['mean']:.4f} ± {agg['p90_tanimoto']['std']:.4f}` p90"
                )
                lines.append(
                    f"- Drug high-similarity rates: `>=0.8` = `{agg['frac_tanimoto_ge_0_8']['mean']:.4f} ± {agg['frac_tanimoto_ge_0_8']['std']:.4f}`, "
                    f"`>=0.9` = `{agg['frac_tanimoto_ge_0_9']['mean']:.4f} ± {agg['frac_tanimoto_ge_0_9']['std']:.4f}`"
                )
                lines.append(
                    f"- Murcko scaffold match rate: `{agg['scaffold_match_rate']['mean']:.4f} ± {agg['scaffold_match_rate']['std']:.4f}`"
                )
            else:
                lines.append(
                    f"- Target nearest identity: `{agg['median_identity']['mean']:.4f} ± {agg['median_identity']['std']:.4f}` median, "
                    f"`{agg['p90_identity']['mean']:.4f} ± {agg['p90_identity']['std']:.4f}` p90"
                )
                lines.append(
                    f"- Target identity rates: `>=0.4` = `{agg['frac_identity_ge_0_4']['mean']:.4f} ± {agg['frac_identity_ge_0_4']['std']:.4f}`, "
                    f"`>=0.6` = `{agg['frac_identity_ge_0_6']['mean']:.4f} ± {agg['frac_identity_ge_0_6']['std']:.4f}`, "
                    f"`>=0.8` = `{agg['frac_identity_ge_0_8']['mean']:.4f} ± {agg['frac_identity_ge_0_8']['std']:.4f}`"
                )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    results: dict[str, dict] = {}
    for split in args.splits:
        split_dir = args.resource_base_dir / args.dataset / split
        payload = {"dataset": args.dataset, "split": split, "entities": {}}
        for entity_type in SPLIT_ENTITY_PLAN.get(split, ()):
            seed_records = []
            for seed in args.seeds:
                seed_dir = split_dir / f"seed{seed}"
                train_df = pd.read_csv(seed_dir / "train.csv")
                test_df = pd.read_csv(seed_dir / "test.csv")
                if entity_type == "drug":
                    diag = analyze_drug_split(train_df, test_df)
                else:
                    diag = analyze_target_split(train_df, test_df, shortlist=args.target_shortlist, kmer_dim=args.kmer_dim)
                diag["seed"] = int(seed)
                seed_records.append(diag)
            payload["entities"][entity_type] = {
                "per_seed": seed_records,
                "aggregate": aggregate_seed_stats(seed_records, entity_type),
            }
        results[split] = payload

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(results, indent=2))
    args.output_md.write_text(build_markdown(results))
    print(json.dumps({"saved_json": str(args.output_json), "saved_md": str(args.output_md)}))


if __name__ == "__main__":
    main()
