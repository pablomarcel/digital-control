from __future__ import annotations
import json
from typing import List, Optional, Tuple
import numpy as np

def parse_matrix_string(s: str) -> np.ndarray:
    rows = [r.strip() for r in s.strip().split(";") if r.strip()]
    mat: List[List[complex]] = []
    for r in rows:
        toks = [t for t in r.replace(",", " ").split() if t]
        row: List[complex] = []
        for t in toks:
            t2 = t.replace("i", "j")
            row.append(complex(t2))
        mat.append(row)
    ncols = {len(r) for r in mat}
    if len(ncols) != 1:
        raise ValueError(f"Non-rectangular matrix: row lengths = {sorted(ncols)}")
    return np.array(mat, dtype=complex)

def load_from_json(path: str) -> Tuple[np.ndarray, np.ndarray, bool, Optional[np.ndarray], Optional[np.ndarray]]:
    with open(path, "r") as f:
        obj = json.load(f)
    if "A" not in obj or "B" not in obj:
        raise ValueError("JSON must contain keys 'A' and 'B'.")
    A = np.array(obj["A"], dtype=complex)
    B = np.array(obj["B"], dtype=complex)
    discrete = bool(obj.get("discrete", False))
    C = np.array(obj["C"], dtype=complex) if "C" in obj else None
    D = np.array(obj["D"], dtype=complex) if "D" in obj else None
    return A, B, discrete, C, D
