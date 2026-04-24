
from __future__ import annotations
import json, os
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

def parse_matrix_string(s: str) -> np.ndarray:
    rows = [r.strip() for r in s.strip().split(";") if r.strip()]
    mat = []
    for r in rows:
        toks = [t for t in r.replace(",", " ").split() if t]
        row = []
        for t in toks:
            t2 = t.replace("i", "j")
            row.append(complex(t2))
        mat.append(row)
    ncols = {len(r) for r in mat}
    if len(ncols) != 1:
        raise ValueError(f"Non-rectangular matrix: row lengths = {sorted(ncols)}")
    return np.array(mat, dtype=complex)

def load_from_json(path: str):
    with open(path, "r") as f:
        obj = json.load(f)
    if "A" not in obj or "C" not in obj:
        raise ValueError("JSON must contain 'A' and 'C'.")
    A = np.array(obj["A"], dtype=complex)
    C = np.array(obj["C"], dtype=complex)
    discrete = bool(obj.get("discrete", False))
    return A, C, discrete

def save_json(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
