from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

LOCAL_BENCHMARK_DIR = Path("data/tdc_benchmark/dti_dg_group")
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
import torch
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.cluster import MiniBatchKMeans
from torch.utils.data import Dataset
from tqdm import tqdm

from tdc.multi_pred import DTI

from .featurizers import sequence_to_hashed_kmers, smiles_to_morgan


def y_to_pkd(y: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=np.float32)
    y = np.clip(y, 1e-12, None)
    return -np.log10(y / 1e9)


def patent_log_nm_to_pkd(y: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=np.float32)
    return 9.0 - (y / np.log(10.0))


def affinity_to_pkd(dataset: str, y: np.ndarray) -> np.ndarray:
    if dataset == "BindingDB_patent":
        return patent_log_nm_to_pkd(y)
    return y_to_pkd(y)


def parse_local_temporal_split(split: str, default_split: str, available_valid_years: list[int]) -> tuple[int, list[str]]:
    if not split.startswith(default_split):
        raise ValueError(f"Unsupported local benchmark split: {split}")

    valid_year = max(available_valid_years)
    suffix = split[len(default_split):]
    modifiers: list[str] = []
    for modifier in ["_pair_novel", "_drug_novel", "_target_novel"]:
        if suffix.startswith(modifier):
            modifiers.append(modifier[1:])
            suffix = suffix[len(modifier):]

    if suffix == "":
        return valid_year, modifiers
    if suffix.startswith("_v"):
        valid_year = int(suffix[2:])
        if valid_year not in available_valid_years:
            raise ValueError(f"Unsupported patent validation year {valid_year}; available years: {available_valid_years}")
        return valid_year, modifiers
    raise ValueError(f"Unsupported local benchmark split: {split}")


def _apply_temporal_novelty_filter(
    train: pd.DataFrame,
    valid: pd.DataFrame,
    test_frame: pd.DataFrame,
    mode: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = train.copy().reset_index(drop=True)
    valid = valid.copy().reset_index(drop=True)
    test_frame = test_frame.copy().reset_index(drop=True)

    if mode == "pair_novel":
        train_pairs = set((train["Drug_ID"].astype(str) + "||" + train["Target_ID"].astype(str)).tolist())
        valid_pairs = set((valid["Drug_ID"].astype(str) + "||" + valid["Target_ID"].astype(str)).tolist())
        valid_mask = ~(valid["Drug_ID"].astype(str) + "||" + valid["Target_ID"].astype(str)).isin(train_pairs)
        test_mask = ~(test_frame["Drug_ID"].astype(str) + "||" + test_frame["Target_ID"].astype(str)).isin(train_pairs | valid_pairs)
    elif mode == "drug_novel":
        train_drugs = set(train["Drug_ID"].astype(str).tolist())
        valid_drugs = set(valid["Drug_ID"].astype(str).tolist())
        valid_mask = ~valid["Drug_ID"].astype(str).isin(train_drugs)
        test_mask = ~test_frame["Drug_ID"].astype(str).isin(train_drugs | valid_drugs)
    elif mode == "target_novel":
        train_targets = set(train["Target_ID"].astype(str).tolist())
        valid_targets = set(valid["Target_ID"].astype(str).tolist())
        valid_mask = ~valid["Target_ID"].astype(str).isin(train_targets)
        test_mask = ~test_frame["Target_ID"].astype(str).isin(train_targets | valid_targets)
    else:
        raise ValueError(f"Unknown temporal novelty filter: {mode}")

    valid = valid[valid_mask].reset_index(drop=True)
    test_frame = test_frame[test_mask].reset_index(drop=True)
    if len(valid) == 0 or len(test_frame) == 0:
        raise ValueError(f"Temporal novelty filter {mode} produced empty valid/test partition")
    return train, valid, test_frame


def load_local_benchmark_split(dataset: str, split: str) -> Dict[str, pd.DataFrame]:
    if dataset == "BindingDB_patent":
        base_dir = LOCAL_BENCHMARK_DIR / "bindingdb_patent"
        default_split = "patent_temporal"
    elif dataset == "BindingDB_nonpatent_Kd":
        base_dir = LOCAL_BENCHMARK_DIR / "bindingdb_nonpatent_kd"
        default_split = "nonpatent_temporal"
    else:
        raise ValueError(f"Unsupported local benchmark dataset/split: {dataset} / {split}")
    train_val = pd.read_csv(base_dir / "train_val.csv")
    test = pd.read_csv(base_dir / "test.csv")
    train_val["Year"] = train_val["Year"].astype(int)
    test["Year"] = test["Year"].astype(int)
    available_valid_years = sorted(train_val["Year"].unique().tolist())
    valid_year, modifiers = parse_local_temporal_split(split, default_split, available_valid_years)
    full_frame = pd.concat([train_val, test], axis=0, ignore_index=True)
    train = full_frame[full_frame["Year"] < valid_year].reset_index(drop=True)
    valid = full_frame[full_frame["Year"] == valid_year].reset_index(drop=True)
    test_frame = full_frame[full_frame["Year"] > valid_year].reset_index(drop=True)
    for modifier in modifiers:
        train, valid, test_frame = _apply_temporal_novelty_filter(train, valid, test_frame, modifier)
    if len(valid) == 0 or len(test_frame) == 0:
        raise ValueError(f"Patent split {split} produced empty valid/test partition")
    return {"train": train, "valid": valid, "test": test_frame}


def split_dataframe(dataset: str, split: str, seed: int, frac: Iterable[float]) -> Dict[str, pd.DataFrame]:
    if dataset in {"BindingDB_patent", "BindingDB_nonpatent_Kd"}:
        return load_local_benchmark_split(dataset, split)

    data = DTI(name=dataset)
    if split == "scaffold_drug":
        return scaffold_split(data.get_data(), seed=seed, frac=list(frac))
    if split == "warm":
        result = data.get_split(method="random", seed=seed, frac=list(frac))
    elif split == "unseen_drug":
        result = data.get_split(method="cold_split", seed=seed, frac=list(frac), column_name="Drug_ID")
    elif split == "unseen_target":
        result = data.get_split(method="cold_split", seed=seed, frac=list(frac), column_name="Target_ID")
    elif split == "blind_start":
        result = data.get_split(method="cold_split", seed=seed, frac=list(frac), column_name=["Drug_ID", "Target_ID"])
    else:
        raise ValueError(f"Unknown split: {split}")
    return result


def _murcko_scaffold(smiles: str) -> str:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return f"invalid::{smiles}"
    scaffold = MurckoScaffold.MurckoScaffoldSmiles(mol=mol)
    return scaffold if scaffold else f"noscaffold::{smiles}"


def scaffold_split(frame: pd.DataFrame, seed: int, frac: list[float]) -> Dict[str, pd.DataFrame]:
    if len(frac) != 3:
        raise ValueError("frac must have length 3")
    frame = frame.copy().reset_index(drop=True)
    drug_frame = frame[["Drug_ID", "Drug"]].drop_duplicates("Drug_ID").reset_index(drop=True)
    drug_frame["scaffold"] = drug_frame["Drug"].astype(str).map(_murcko_scaffold)
    row_counts = frame["Drug_ID"].value_counts().to_dict()
    scaffold_to_drugs = drug_frame.groupby("scaffold")["Drug_ID"].apply(list).to_dict()
    scaffold_items = []
    for scaffold, drug_ids in scaffold_to_drugs.items():
        weight = int(sum(int(row_counts.get(drug_id, 0)) for drug_id in drug_ids))
        scaffold_items.append((scaffold, drug_ids, weight))

    rng = np.random.default_rng(seed)
    rng.shuffle(scaffold_items)

    total_rows = len(frame)
    target_rows = {
        "train": float(total_rows * frac[0]),
        "valid": float(total_rows * frac[1]),
        "test": float(total_rows * frac[2]),
    }
    assigned_rows = {"train": 0, "valid": 0, "test": 0}
    split_drugs = {"train": set(), "valid": set(), "test": set()}

    for _, drug_ids, weight in scaffold_items:
        best_split = None
        best_key = None
        for split_name in ["train", "valid", "test"]:
            new_rows = assigned_rows[split_name] + weight
            change = abs(new_rows - target_rows[split_name]) - abs(assigned_rows[split_name] - target_rows[split_name])
            fill_ratio = assigned_rows[split_name] / max(target_rows[split_name], 1.0)
            key = (change, fill_ratio, assigned_rows[split_name])
            if best_key is None or key < best_key:
                best_key = key
                best_split = split_name
        split_drugs[best_split].update(drug_ids)
        assigned_rows[best_split] += weight

    partitions = {}
    for split_name in ["train", "valid", "test"]:
        partitions[split_name] = frame[frame["Drug_ID"].isin(split_drugs[split_name])].reset_index(drop=True)
        if len(partitions[split_name]) == 0:
            raise ValueError(f"scaffold split produced empty {split_name} partition")
    return partitions


def maybe_subsample(df: pd.DataFrame, max_rows: int | None, seed: int) -> pd.DataFrame:
    if max_rows is None or len(df) <= max_rows:
        return df.reset_index(drop=True)
    return df.sample(n=max_rows, random_state=seed).reset_index(drop=True)


def _stable_missing_entity_id(prefix: str, entity_value: object, row_idx: int) -> str:
    if pd.isna(entity_value):
        return f"{prefix}_missing_row_{row_idx}"
    digest = hashlib.sha1(str(entity_value).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_missing_{digest}"


def standardize_entity_ids(frame: pd.DataFrame, id_col: str, value_col: str, prefix: str) -> pd.DataFrame:
    frame = frame.copy()
    normalized_ids = []
    for row_idx, (entity_id, entity_value) in enumerate(zip(frame[id_col].tolist(), frame[value_col].tolist())):
        if pd.isna(entity_id):
            normalized_ids.append(_stable_missing_entity_id(prefix, entity_value, row_idx))
        else:
            normalized_ids.append(str(entity_id))
    frame[id_col] = normalized_ids
    return frame


def build_entity_frame(df_list: List[pd.DataFrame], id_col: str, value_col: str) -> pd.DataFrame:
    frame = pd.concat([df[[id_col, value_col]] for df in df_list], axis=0).drop_duplicates(subset=[id_col]).reset_index(drop=True)
    return frame


def featurize_drugs(frame: pd.DataFrame, n_bits: int, radius: int) -> np.ndarray:
    return np.stack([smiles_to_morgan(smiles, n_bits=n_bits, radius=radius) for smiles in tqdm(frame["Drug"].tolist(), desc="drug feats")])


def featurize_targets(frame: pd.DataFrame, dim: int) -> np.ndarray:
    return np.stack([sequence_to_hashed_kmers(seq, dim=dim) for seq in tqdm(frame["Target"].tolist(), desc="target feats")])


def normalize_rows(x: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(x, axis=1, keepdims=True)
    norm = np.where(norm == 0, 1.0, norm)
    return x / norm


def softmax_rows(x: np.ndarray) -> np.ndarray:
    x = x - np.max(x, axis=1, keepdims=True)
    exp_x = np.exp(x)
    return exp_x / np.clip(np.sum(exp_x, axis=1, keepdims=True), 1e-12, None)


def sparsify_topk_rows(x: np.ndarray, topk: int | None) -> np.ndarray:
    if topk is None or topk <= 0 or topk >= x.shape[1]:
        return x
    top_idx = np.argpartition(x, -topk, axis=1)[:, -topk:]
    mask = np.zeros_like(x, dtype=np.bool_)
    row_idx = np.arange(x.shape[0])[:, None]
    mask[row_idx, top_idx] = True
    sparse = np.where(mask, x, 0.0)
    sparse = sparse / np.clip(np.sum(sparse, axis=1, keepdims=True), 1e-12, None)
    return sparse.astype(np.float32)


def topk_cosine(
    query_x: np.ndarray,
    bank_x: np.ndarray,
    query_ids: np.ndarray,
    bank_ids: np.ndarray,
    k: int,
    chunk_size: int = 512,
) -> Tuple[np.ndarray, np.ndarray]:
    query_x = normalize_rows(query_x).astype(np.float32)
    bank_x = normalize_rows(bank_x).astype(np.float32)
    bank_t = torch.from_numpy(bank_x)
    all_indices = []
    all_scores = []
    for start in range(0, len(query_x), chunk_size):
        end = min(start + chunk_size, len(query_x))
        chunk = torch.from_numpy(query_x[start:end])
        scores = chunk @ bank_t.T
        same = torch.from_numpy((query_ids[start:end, None] == bank_ids[None, :]).astype(np.bool_))
        scores = scores.masked_fill(same, -1e9)
        values, indices = torch.topk(scores, k=min(k, bank_t.shape[0]), dim=1)
        all_indices.append(indices.numpy())
        all_scores.append(values.numpy())
    return np.concatenate(all_indices, axis=0), np.concatenate(all_scores, axis=0)


def entity_stats(train_df: pd.DataFrame, id_col: str, label_col: str) -> pd.DataFrame:
    stats = train_df.groupby(id_col)[label_col].agg(["mean", "count"]).reset_index()
    stats.columns = [id_col, "positive_rate", "support_count"]
    return stats


def build_drug_cluster_weights(
    drug_features: np.ndarray,
    train_drug_bank_idx: np.ndarray,
    num_chemotypes: int,
    seed: int,
    assignment_topk: int | None = 4,
) -> Tuple[np.ndarray, np.ndarray]:
    n_clusters = int(min(max(2, num_chemotypes), len(train_drug_bank_idx)))
    kmeans = MiniBatchKMeans(
        n_clusters=n_clusters,
        random_state=seed,
        n_init=10,
        batch_size=min(2048, max(256, len(train_drug_bank_idx))),
    )
    kmeans.fit(drug_features[train_drug_bank_idx])
    distances = kmeans.transform(drug_features).astype(np.float32)
    scale = float(np.mean(distances) + 1e-6)
    weights = softmax_rows(-distances / scale).astype(np.float32)
    weights = sparsify_topk_rows(weights, assignment_topk)
    return weights, kmeans.cluster_centers_.astype(np.float32)


def build_target_cluster_profiles(
    train_df: pd.DataFrame,
    drug_id_to_index: Dict[object, int],
    target_id_to_index: Dict[object, int],
    drug_cluster_weights: np.ndarray,
    num_chemotypes: int,
    alpha: float = 1.0,
    shrinkage: float = 8.0,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    positive = np.zeros((len(target_id_to_index), num_chemotypes), dtype=np.float32)
    total = np.zeros((len(target_id_to_index), num_chemotypes), dtype=np.float32)
    for row in train_df.itertuples(index=False):
        target_idx = target_id_to_index[row.Target_ID]
        drug_idx = drug_id_to_index[row.Drug_ID]
        weights = drug_cluster_weights[drug_idx]
        positive[target_idx] += weights * float(row.label)
        total[target_idx] += weights
    global_positive = np.sum(positive, axis=0, keepdims=True)
    global_total = np.sum(total, axis=0, keepdims=True)
    chemotype_prior = (global_positive + alpha) / (global_total + 2.0 * alpha)
    local_prob = (positive + alpha) / (total + 2.0 * alpha)
    shrink = total / (total + shrinkage)
    profile = (local_prob - chemotype_prior) * shrink
    mask = (np.sum(total, axis=1) > 0).astype(np.float32)
    return profile.astype(np.float32), mask.astype(np.float32), chemotype_prior.squeeze(0).astype(np.float32)


@dataclass
class SplitArtifacts:
    train_df: pd.DataFrame
    valid_df: pd.DataFrame
    test_df: pd.DataFrame
    drug_frame: pd.DataFrame
    target_frame: pd.DataFrame
    drug_features: np.ndarray
    target_features: np.ndarray
    drug_id_to_index: Dict[object, int]
    target_id_to_index: Dict[object, int]
    drug_neighbor_indices: np.ndarray
    drug_neighbor_scores: np.ndarray
    target_neighbor_indices: np.ndarray
    target_neighbor_scores: np.ndarray
    drug_neighbor_stats: np.ndarray
    target_neighbor_stats: np.ndarray
    train_drug_bank_idx: np.ndarray
    train_target_bank_idx: np.ndarray
    drug_cluster_weights: np.ndarray
    target_cluster_profiles: np.ndarray
    target_cluster_mask: np.ndarray
    chemotype_prior: np.ndarray


def prepare_split_artifacts(
    dataset: str,
    split: str,
    seed: int,
    frac: Iterable[float],
    pkd_threshold: float,
    drug_bits: int,
    drug_radius: int,
    target_dim: int,
    k: int,
    cache_dir: Path,
    num_chemotypes: int = 32,
    chemotype_topk: int = 4,
    profile_shrinkage: float = 8.0,
    max_train: int | None = None,
    max_valid: int | None = None,
    max_test: int | None = None,
) -> SplitArtifacts:
    cache_dir.mkdir(parents=True, exist_ok=True)
    split_frames = split_dataframe(dataset, split, seed, frac)
    train_df = maybe_subsample(split_frames["train"], max_train, seed)
    valid_df = maybe_subsample(split_frames["valid"], max_valid, seed + 1)
    test_df = maybe_subsample(split_frames["test"], max_test, seed + 2)

    train_df = standardize_entity_ids(train_df, "Drug_ID", "Drug", "drug")
    valid_df = standardize_entity_ids(valid_df, "Drug_ID", "Drug", "drug")
    test_df = standardize_entity_ids(test_df, "Drug_ID", "Drug", "drug")
    train_df = standardize_entity_ids(train_df, "Target_ID", "Target", "target")
    valid_df = standardize_entity_ids(valid_df, "Target_ID", "Target", "target")
    test_df = standardize_entity_ids(test_df, "Target_ID", "Target", "target")

    for frame in [train_df, valid_df, test_df]:
        frame["pKd"] = affinity_to_pkd(dataset, frame["Y"].to_numpy())
        frame["label"] = (frame["pKd"] >= pkd_threshold).astype(np.int64)

    drug_frame = build_entity_frame([train_df, valid_df, test_df], "Drug_ID", "Drug")
    target_frame = build_entity_frame([train_df, valid_df, test_df], "Target_ID", "Target")

    sample_tag = f"seed{seed}_mt{max_train if max_train is not None else 'all'}_mv{max_valid if max_valid is not None else 'all'}_mte{max_test if max_test is not None else 'all'}"
    chemotype_tag = f"chemotypes{num_chemotypes}_top{chemotype_topk}_shr{str(profile_shrinkage).replace('.', 'p')}"
    drug_cache = cache_dir / f"{dataset}_{split}_{sample_tag}_drug_bits{drug_bits}_r{drug_radius}.npy"
    target_cache = cache_dir / f"{dataset}_{split}_{sample_tag}_target_dim{target_dim}.npy"
    chemotype_cache = cache_dir / f"{dataset}_{split}_{sample_tag}_{chemotype_tag}_drug_weights.npy"
    target_profile_cache = cache_dir / f"{dataset}_{split}_{sample_tag}_{chemotype_tag}_target_profiles.npy"
    target_mask_cache = cache_dir / f"{dataset}_{split}_{sample_tag}_{chemotype_tag}_target_mask.npy"
    chemotype_prior_cache = cache_dir / f"{dataset}_{split}_{sample_tag}_{chemotype_tag}_prior.npy"

    if drug_cache.exists():
        drug_features = np.load(drug_cache)
        if drug_features.shape[0] != len(drug_frame):
            drug_features = featurize_drugs(drug_frame, n_bits=drug_bits, radius=drug_radius)
            np.save(drug_cache, drug_features)
    else:
        drug_features = featurize_drugs(drug_frame, n_bits=drug_bits, radius=drug_radius)
        np.save(drug_cache, drug_features)

    if target_cache.exists():
        target_features = np.load(target_cache)
        if target_features.shape[0] != len(target_frame):
            target_features = featurize_targets(target_frame, dim=target_dim)
            np.save(target_cache, target_features)
    else:
        target_features = featurize_targets(target_frame, dim=target_dim)
        np.save(target_cache, target_features)

    drug_id_to_index = {drug_id: idx for idx, drug_id in enumerate(drug_frame["Drug_ID"].tolist())}
    target_id_to_index = {target_id: idx for idx, target_id in enumerate(target_frame["Target_ID"].tolist())}

    train_drug_ids = train_df["Drug_ID"].drop_duplicates().tolist()
    train_target_ids = train_df["Target_ID"].drop_duplicates().tolist()
    train_drug_bank_idx = np.asarray([drug_id_to_index[x] for x in train_drug_ids], dtype=np.int64)
    train_target_bank_idx = np.asarray([target_id_to_index[x] for x in train_target_ids], dtype=np.int64)

    drug_stat_frame = entity_stats(train_df, "Drug_ID", "label")
    target_stat_frame = entity_stats(train_df, "Target_ID", "label")
    drug_stat_lookup = {
        row["Drug_ID"]: (float(row["positive_rate"]), float(np.log1p(row["support_count"])))
        for _, row in drug_stat_frame.iterrows()
    }
    target_stat_lookup = {
        row["Target_ID"]: (float(row["positive_rate"]), float(np.log1p(row["support_count"])))
        for _, row in target_stat_frame.iterrows()
    }

    drug_neighbor_indices, drug_neighbor_scores = topk_cosine(
        drug_features,
        drug_features[train_drug_bank_idx],
        drug_frame["Drug_ID"].to_numpy(),
        np.asarray(train_drug_ids),
        k=k,
    )
    target_neighbor_indices, target_neighbor_scores = topk_cosine(
        target_features,
        target_features[train_target_bank_idx],
        target_frame["Target_ID"].to_numpy(),
        np.asarray(train_target_ids),
        k=k,
    )

    train_drug_bank_ids = np.asarray(train_drug_ids)
    train_target_bank_ids = np.asarray(train_target_ids)

    drug_neighbor_stats = np.zeros((len(drug_frame), drug_neighbor_indices.shape[1], 3), dtype=np.float32)
    target_neighbor_stats = np.zeros((len(target_frame), target_neighbor_indices.shape[1], 3), dtype=np.float32)

    for i in range(len(drug_frame)):
        for j, local_idx in enumerate(drug_neighbor_indices[i]):
            drug_id = train_drug_bank_ids[local_idx]
            rate, support = drug_stat_lookup.get(drug_id, (0.0, 0.0))
            drug_neighbor_stats[i, j] = (rate, support, float(drug_neighbor_scores[i, j]))
        drug_neighbor_indices[i] = train_drug_bank_idx[drug_neighbor_indices[i]]

    for i in range(len(target_frame)):
        for j, local_idx in enumerate(target_neighbor_indices[i]):
            target_id = train_target_bank_ids[local_idx]
            rate, support = target_stat_lookup.get(target_id, (0.0, 0.0))
            target_neighbor_stats[i, j] = (rate, support, float(target_neighbor_scores[i, j]))
        target_neighbor_indices[i] = train_target_bank_idx[target_neighbor_indices[i]]

    if chemotype_cache.exists():
        drug_cluster_weights = np.load(chemotype_cache)
        if drug_cluster_weights.shape[0] != len(drug_frame):
            drug_cluster_weights, _ = build_drug_cluster_weights(
                drug_features=drug_features,
                train_drug_bank_idx=train_drug_bank_idx,
                num_chemotypes=num_chemotypes,
                seed=seed,
                assignment_topk=chemotype_topk,
            )
            np.save(chemotype_cache, drug_cluster_weights)
    else:
        drug_cluster_weights, _ = build_drug_cluster_weights(
            drug_features=drug_features,
            train_drug_bank_idx=train_drug_bank_idx,
            num_chemotypes=num_chemotypes,
            seed=seed,
            assignment_topk=chemotype_topk,
        )
        np.save(chemotype_cache, drug_cluster_weights)

    effective_chemotypes = int(drug_cluster_weights.shape[1])
    if target_profile_cache.exists() and target_mask_cache.exists() and chemotype_prior_cache.exists():
        target_cluster_profiles = np.load(target_profile_cache)
        target_cluster_mask = np.load(target_mask_cache)
        chemotype_prior = np.load(chemotype_prior_cache)
        if target_cluster_profiles.shape[0] != len(target_frame) or target_cluster_mask.shape[0] != len(target_frame):
            target_cluster_profiles, target_cluster_mask, chemotype_prior = build_target_cluster_profiles(
                train_df=train_df,
                drug_id_to_index=drug_id_to_index,
                target_id_to_index=target_id_to_index,
                drug_cluster_weights=drug_cluster_weights,
                num_chemotypes=effective_chemotypes,
                shrinkage=profile_shrinkage,
            )
            np.save(target_profile_cache, target_cluster_profiles)
            np.save(target_mask_cache, target_cluster_mask)
            np.save(chemotype_prior_cache, chemotype_prior)
    else:
        target_cluster_profiles, target_cluster_mask, chemotype_prior = build_target_cluster_profiles(
            train_df=train_df,
            drug_id_to_index=drug_id_to_index,
            target_id_to_index=target_id_to_index,
            drug_cluster_weights=drug_cluster_weights,
            num_chemotypes=effective_chemotypes,
            shrinkage=profile_shrinkage,
        )
        np.save(target_profile_cache, target_cluster_profiles)
        np.save(target_mask_cache, target_cluster_mask)
        np.save(chemotype_prior_cache, chemotype_prior)

    meta_path = cache_dir / f"{dataset}_{split}_{sample_tag}_meta.json"
    meta_path.write_text(
        json.dumps(
            {
                "dataset": dataset,
                "split": split,
                "seed": seed,
                "train_rows": len(train_df),
                "valid_rows": len(valid_df),
                "test_rows": len(test_df),
                "train_drugs": int(train_df["Drug_ID"].nunique()),
                "train_targets": int(train_df["Target_ID"].nunique()),
                "num_chemotypes": effective_chemotypes,
                "chemotype_topk": chemotype_topk,
                "profile_shrinkage": profile_shrinkage,
            },
            indent=2,
        )
    )

    return SplitArtifacts(
        train_df=train_df.reset_index(drop=True),
        valid_df=valid_df.reset_index(drop=True),
        test_df=test_df.reset_index(drop=True),
        drug_frame=drug_frame,
        target_frame=target_frame,
        drug_features=drug_features.astype(np.float32),
        target_features=target_features.astype(np.float32),
        drug_id_to_index=drug_id_to_index,
        target_id_to_index=target_id_to_index,
        drug_neighbor_indices=drug_neighbor_indices.astype(np.int64),
        drug_neighbor_scores=drug_neighbor_scores.astype(np.float32),
        target_neighbor_indices=target_neighbor_indices.astype(np.int64),
        target_neighbor_scores=target_neighbor_scores.astype(np.float32),
        drug_neighbor_stats=drug_neighbor_stats,
        target_neighbor_stats=target_neighbor_stats,
        train_drug_bank_idx=train_drug_bank_idx,
        train_target_bank_idx=train_target_bank_idx,
        drug_cluster_weights=drug_cluster_weights.astype(np.float32),
        target_cluster_profiles=target_cluster_profiles.astype(np.float32),
        target_cluster_mask=target_cluster_mask.astype(np.float32),
        chemotype_prior=chemotype_prior.astype(np.float32),
    )


class InteractionDataset(Dataset):
    def __init__(self, frame: pd.DataFrame, artifacts: SplitArtifacts):
        self.frame = frame.reset_index(drop=True)
        self.artifacts = artifacts

    def __len__(self) -> int:
        return len(self.frame)

    def __getitem__(self, idx: int) -> Dict[str, np.ndarray]:
        row = self.frame.iloc[idx]
        drug_idx = self.artifacts.drug_id_to_index[row["Drug_ID"]]
        target_idx = self.artifacts.target_id_to_index[row["Target_ID"]]

        overlap_score = min(
            float(self.artifacts.drug_neighbor_scores[drug_idx, 0]),
            float(self.artifacts.target_neighbor_scores[target_idx, 0]),
        )

        return {
            "drug_x": self.artifacts.drug_features[drug_idx],
            "target_x": self.artifacts.target_features[target_idx],
            "drug_neighbors": self.artifacts.drug_features[self.artifacts.drug_neighbor_indices[drug_idx]],
            "target_neighbors": self.artifacts.target_features[self.artifacts.target_neighbor_indices[target_idx]],
            "drug_neighbor_stats": self.artifacts.drug_neighbor_stats[drug_idx],
            "target_neighbor_stats": self.artifacts.target_neighbor_stats[target_idx],
            "drug_cluster_weights": self.artifacts.drug_cluster_weights[drug_idx],
            "target_cluster_profile": self.artifacts.target_cluster_profiles[target_idx],
            "target_cluster_mask": np.asarray(self.artifacts.target_cluster_mask[target_idx], dtype=np.float32),
            "label": np.int64(row["label"]),
            "overlap_score": np.float32(overlap_score),
        }


def collate_batch(items: List[Dict[str, np.ndarray]]) -> Dict[str, torch.Tensor]:
    batch = {}
    keys = items[0].keys()
    for key in keys:
        arr = np.stack([item[key] for item in items], axis=0)
        if key in {"label", "overlap_score", "target_cluster_mask"}:
            batch[key] = torch.from_numpy(arr.astype(np.float32))
        else:
            batch[key] = torch.from_numpy(arr.astype(np.float32))
    return batch
