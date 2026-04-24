
from __future__ import annotations
import json
import numpy as np
from typing import Optional, Tuple

def parse_matrix(text: Optional[str]) -> Optional[np.ndarray]:
    if text is None:
        return None
    s = text.strip()
    if not s:
        return None
    rows = []
    for row in s.split(";"):
        vals = [complex(x) for x in row.replace(",", " ").split()]
        rows.append(vals)
    ncols = {len(r) for r in rows}
    if len(ncols) != 1:
        raise ValueError("All rows must have the same number of columns.")
    arr = np.array(rows, dtype=complex)
    return arr

def load_from_json(path: str) -> Tuple[np.ndarray, Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
    with open(path, "r") as f:
        data = json.load(f)
    A = np.array(data["A"], dtype=complex)
    B = np.array(data["B"], dtype=complex) if "B" in data and data["B"] is not None else None
    C = np.array(data["C"], dtype=complex) if "C" in data and data["C"] is not None else None
    D = np.array(data["D"], dtype=complex) if "D" in data and data["D"] is not None else None
    if B is not None and B.ndim == 1: B = B.reshape(-1, 1)
    if C is not None and C.ndim == 1: C = C.reshape(1, -1)
    if D is not None:
        if D.ndim == 0: D = D.reshape(1, 1)
        elif D.ndim == 1: D = D.reshape(1, -1)
    return A, B, C, D
