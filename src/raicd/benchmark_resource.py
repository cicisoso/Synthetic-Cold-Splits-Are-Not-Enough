from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .data import SplitArtifacts, prepare_split_artifacts


RESOURCE_VERSION = 1


@dataclass
class ExportedBenchmarkResource:
    resource_dir: Path
    train_csv: Path
    valid_csv: Path
    test_csv: Path
    all_csv: Path
    drugs_csv: Path
    targets_csv: Path
    manifest_json: Path


def benchmark_resource_dir(base_dir: Path, dataset: str, split: str, seed: int) -> Path:
    return base_dir / dataset / split / f"seed{seed}"


def _partition_frame(
    frame: pd.DataFrame,
    artifacts: SplitArtifacts,
    dataset: str,
    split: str,
    seed: int,
    partition: str,
) -> pd.DataFrame:
    frame = frame.copy().reset_index(drop=True)
    drug_idx = frame["Drug_ID"].map(artifacts.drug_id_to_index).to_numpy(dtype=np.int64)
    target_idx = frame["Target_ID"].map(artifacts.target_id_to_index).to_numpy(dtype=np.int64)
    drug_overlap = artifacts.drug_neighbor_scores[drug_idx, 0].astype(np.float32)
    target_overlap = artifacts.target_neighbor_scores[target_idx, 0].astype(np.float32)
    frame.insert(0, "example_id", [f"{dataset}|{split}|seed{seed}|{partition}|{idx}" for idx in range(len(frame))])
    frame.insert(1, "dataset", dataset)
    frame.insert(2, "split", split)
    frame.insert(3, "seed", int(seed))
    frame.insert(4, "partition", partition)
    frame["drug_overlap"] = drug_overlap
    frame["target_overlap"] = target_overlap
    frame["overlap_score"] = np.minimum(drug_overlap, target_overlap).astype(np.float32)
    if "Year" not in frame.columns:
        frame["Year"] = np.nan

    ordered = [
        "example_id",
        "dataset",
        "split",
        "seed",
        "partition",
        "Drug_ID",
        "Target_ID",
        "Drug",
        "Target",
        "Y",
        "pKd",
        "label",
        "Year",
        "drug_overlap",
        "target_overlap",
        "overlap_score",
    ]
    extra = [col for col in frame.columns if col not in ordered]
    return frame[ordered + extra]


def _entity_exports(artifacts: SplitArtifacts) -> tuple[pd.DataFrame, pd.DataFrame]:
    drugs = artifacts.drug_frame.copy().rename(columns={"Drug_ID": "drug_id", "Drug": "drug_smile"})
    drugs["drug_smiles"] = drugs["drug_smile"]
    drugs["Drug_ID"] = drugs["drug_id"]
    drugs["Drug"] = drugs["drug_smile"]
    drugs = drugs[["drug_id", "drug_smile", "drug_smiles", "Drug_ID", "Drug"]]

    targets = artifacts.target_frame.copy().rename(columns={"Target_ID": "prot_id", "Target": "prot_seq"})
    targets["Target_ID"] = targets["prot_id"]
    targets["Target"] = targets["prot_seq"]
    targets = targets[["prot_id", "prot_seq", "Target_ID", "Target"]]
    return drugs, targets


def _pair_exports(frame: pd.DataFrame) -> pd.DataFrame:
    pairs = frame.copy().rename(columns={"Drug_ID": "drug_id", "Target_ID": "prot_id"})
    ordered = [
        "example_id",
        "partition",
        "drug_id",
        "prot_id",
        "label",
        "Y",
        "pKd",
        "Year",
        "overlap_score",
    ]
    return pairs[ordered]


def export_benchmark_resource(
    dataset: str,
    split: str,
    seed: int,
    output_base_dir: Path,
    frac: Iterable[float],
    cache_dir: Path,
    pkd_threshold: float = 7.0,
    drug_bits: int = 2048,
    drug_radius: int = 2,
    target_dim: int = 2048,
    topk: int = 8,
    num_chemotypes: int = 32,
    chemotype_topk: int = 4,
    profile_shrinkage: float = 8.0,
    max_train: int | None = None,
    max_valid: int | None = None,
    max_test: int | None = None,
    force: bool = False,
) -> ExportedBenchmarkResource:
    resource_dir = benchmark_resource_dir(output_base_dir, dataset, split, seed)
    manifest_json = resource_dir / "manifest.json"
    if manifest_json.exists() and not force:
        return ExportedBenchmarkResource(
            resource_dir=resource_dir,
            train_csv=resource_dir / "train.csv",
            valid_csv=resource_dir / "valid.csv",
            test_csv=resource_dir / "test.csv",
            all_csv=resource_dir / "all.csv",
            drugs_csv=resource_dir / "drugs.csv",
            targets_csv=resource_dir / "targets.csv",
            manifest_json=manifest_json,
        )

    artifacts = prepare_split_artifacts(
        dataset=dataset,
        split=split,
        seed=seed,
        frac=frac,
        pkd_threshold=pkd_threshold,
        drug_bits=drug_bits,
        drug_radius=drug_radius,
        target_dim=target_dim,
        k=topk,
        cache_dir=cache_dir,
        num_chemotypes=num_chemotypes,
        chemotype_topk=chemotype_topk,
        profile_shrinkage=profile_shrinkage,
        max_train=max_train,
        max_valid=max_valid,
        max_test=max_test,
    )

    resource_dir.mkdir(parents=True, exist_ok=True)

    train_frame = _partition_frame(artifacts.train_df, artifacts, dataset, split, seed, "train")
    valid_frame = _partition_frame(artifacts.valid_df, artifacts, dataset, split, seed, "valid")
    test_frame = _partition_frame(artifacts.test_df, artifacts, dataset, split, seed, "test")
    all_frame = pd.concat([train_frame, valid_frame, test_frame], axis=0, ignore_index=True)
    drugs, targets = _entity_exports(artifacts)

    train_csv = resource_dir / "train.csv"
    valid_csv = resource_dir / "valid.csv"
    test_csv = resource_dir / "test.csv"
    all_csv = resource_dir / "all.csv"
    drugs_csv = resource_dir / "drugs.csv"
    targets_csv = resource_dir / "targets.csv"

    train_frame.to_csv(train_csv, index=False)
    valid_frame.to_csv(valid_csv, index=False)
    test_frame.to_csv(test_csv, index=False)
    all_frame.to_csv(all_csv, index=False)
    drugs.to_csv(drugs_csv, index=False)
    targets.to_csv(targets_csv, index=False)
    _pair_exports(train_frame).to_csv(resource_dir / "train_pairs.csv", index=False)
    _pair_exports(valid_frame).to_csv(resource_dir / "valid_pairs.csv", index=False)
    _pair_exports(test_frame).to_csv(resource_dir / "test_pairs.csv", index=False)
    _pair_exports(all_frame).to_csv(resource_dir / "all_pairs.csv", index=False)

    manifest = {
        "resource_version": RESOURCE_VERSION,
        "dataset": dataset,
        "split": split,
        "seed": int(seed),
        "frac": list(frac),
        "pkd_threshold": float(pkd_threshold),
        "train_rows": int(len(train_frame)),
        "valid_rows": int(len(valid_frame)),
        "test_rows": int(len(test_frame)),
        "train_positive_rate": float(train_frame["label"].mean()),
        "valid_positive_rate": float(valid_frame["label"].mean()),
        "test_positive_rate": float(test_frame["label"].mean()),
        "unique_drugs": int(drugs["drug_id"].nunique()),
        "unique_targets": int(targets["prot_id"].nunique()),
        "paths": {
            "train_csv": str(train_csv),
            "valid_csv": str(valid_csv),
            "test_csv": str(test_csv),
            "all_csv": str(all_csv),
            "drugs_csv": str(drugs_csv),
            "targets_csv": str(targets_csv),
        },
    }
    manifest_json.write_text(json.dumps(manifest, indent=2))
    return ExportedBenchmarkResource(
        resource_dir=resource_dir,
        train_csv=train_csv,
        valid_csv=valid_csv,
        test_csv=test_csv,
        all_csv=all_csv,
        drugs_csv=drugs_csv,
        targets_csv=targets_csv,
        manifest_json=manifest_json,
    )


def ensure_benchmark_resource(
    dataset: str,
    split: str,
    seed: int,
    output_base_dir: Path,
    frac: Iterable[float],
    cache_dir: Path,
    **kwargs,
) -> ExportedBenchmarkResource:
    return export_benchmark_resource(
        dataset=dataset,
        split=split,
        seed=seed,
        output_base_dir=output_base_dir,
        frac=frac,
        cache_dir=cache_dir,
        **kwargs,
    )
