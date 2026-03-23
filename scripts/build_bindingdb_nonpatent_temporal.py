#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


USECOLS = [
    "BindingDB MonomerID",
    "Ligand SMILES",
    "Kd (nM)",
    "Patent Number",
    "Date of publication",
    "Number of Protein Chains in Target (>1 implies a multichain complex)",
    "BindingDB Target Chain Sequence 1",
    "UniProt (SwissProt) Primary ID of Target Chain 1",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a non-patent temporal Kd benchmark from the official BindingDB TSV.")
    parser.add_argument("--input-zip", type=Path, default=Path("data/external/BindingDB_All_202603_tsv.zip"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/tdc_benchmark/dti_dg_group/bindingdb_nonpatent_kd"))
    parser.add_argument("--valid-year", type=int, default=2019)
    parser.add_argument("--chunksize", type=int, default=100000)
    parser.add_argument("--min-test-year", type=int, default=None)
    return parser.parse_args()


def _normalize_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    chunk = chunk.copy()
    chunk["Kd (nM)"] = pd.to_numeric(chunk["Kd (nM)"], errors="coerce")
    chunk["num_chains"] = pd.to_numeric(
        chunk["Number of Protein Chains in Target (>1 implies a multichain complex)"],
        errors="coerce",
    )
    patent = chunk["Patent Number"].fillna("").astype(str).str.strip()
    chunk["year"] = pd.to_datetime(chunk["Date of publication"], errors="coerce").dt.year
    chunk = chunk[
        chunk["Kd (nM)"].notna()
        & (chunk["Kd (nM)"] > 0)
        & chunk["Ligand SMILES"].notna()
        & chunk["BindingDB Target Chain Sequence 1"].notna()
        & chunk["year"].notna()
        & (chunk["num_chains"] == 1)
        & (patent == "")
    ].copy()
    chunk["Drug_ID"] = chunk["BindingDB MonomerID"].astype(str)
    chunk["Drug"] = chunk["Ligand SMILES"].astype(str)
    chunk["Target_ID"] = (
        chunk["UniProt (SwissProt) Primary ID of Target Chain 1"]
        .fillna("")
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
    )
    missing_mask = chunk["Target_ID"].isna()
    if missing_mask.any():
        chunk.loc[missing_mask, "Target_ID"] = [
            f"target_missing_{idx}" for idx in chunk.index[missing_mask].tolist()
        ]
    chunk["Target"] = chunk["BindingDB Target Chain Sequence 1"].astype(str)
    chunk["Y"] = chunk["Kd (nM)"].astype(float)
    chunk["Year"] = chunk["year"].astype(int)
    return chunk[["Drug_ID", "Drug", "Target_ID", "Target", "Y", "Year"]]


def main() -> None:
    args = parse_args()
    frames = []
    for chunk in pd.read_csv(
        args.input_zip,
        sep="\t",
        compression="zip",
        usecols=USECOLS,
        chunksize=args.chunksize,
        low_memory=False,
    ):
        frames.append(_normalize_chunk(chunk))

    frame = pd.concat(frames, axis=0, ignore_index=True).drop_duplicates().reset_index(drop=True)
    if args.min_test_year is not None:
        frame = frame[frame["Year"] >= args.min_test_year].reset_index(drop=True)

    train_val = frame[frame["Year"] <= args.valid_year].reset_index(drop=True)
    test = frame[frame["Year"] > args.valid_year].reset_index(drop=True)
    if len(test) == 0:
        raise ValueError("Empty test split after applying the chosen valid year.")
    if len(train_val[train_val["Year"] == args.valid_year]) == 0:
        raise ValueError("Chosen valid year does not exist in the filtered dataset.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "train_val.csv").write_text(train_val.to_csv(index=False))
    (args.output_dir / "test.csv").write_text(test.to_csv(index=False))
    summary = {
        "input_zip": str(args.input_zip),
        "valid_year": int(args.valid_year),
        "min_test_year": int(args.min_test_year) if args.min_test_year is not None else None,
        "rows_total": int(len(frame)),
        "rows_train_val": int(len(train_val)),
        "rows_test": int(len(test)),
        "year_counts": {str(int(year)): int(count) for year, count in frame["Year"].value_counts().sort_index().items()},
        "positive_rate_valid_year": None,
    }
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
