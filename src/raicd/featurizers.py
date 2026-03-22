from __future__ import annotations

import hashlib
from typing import Iterable

import numpy as np
from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem


AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"


def smiles_to_morgan(smiles: str, n_bits: int = 2048, radius: int = 2) -> np.ndarray:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return np.zeros(n_bits, dtype=np.float32)
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    arr = np.zeros((n_bits,), dtype=np.float32)
    DataStructs.ConvertToNumpyArray(fp, arr)
    return arr


def _stable_hash(token: str, dim: int) -> int:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "little") % dim


def sequence_to_hashed_kmers(
    sequence: str,
    dim: int = 2048,
    k_sizes: Iterable[int] = (1, 2, 3),
) -> np.ndarray:
    vec = np.zeros(dim, dtype=np.float32)
    if not sequence:
        return vec
    seq = "".join(ch for ch in sequence.upper() if ch in AMINO_ACIDS)
    if not seq:
        return vec
    for k in k_sizes:
        if len(seq) < k:
            continue
        for i in range(len(seq) - k + 1):
            token = f"{k}:{seq[i:i + k]}"
            vec[_stable_hash(token, dim)] += 1.0
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec
