from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List
import numpy as np

def parse_matrix(s: str | None) -> np.ndarray | None:
    if s is None:
        return None
    s = s.strip().replace(",", " ")
    rows = [r for r in s.split(";") if r.strip()]
    data: List[List[complex]] = []
    for r in rows:
        toks = [t for t in r.strip().split() if t]
        data.append([complex(t) for t in toks])
    return np.array(data, dtype=complex)

def parse_poles(s: str, n: int) -> np.ndarray:
    toks = [t for t in s.replace(",", " ").split() if t]
    poles = [complex(t) for t in toks]
    if len(poles) != n:
        raise ValueError(f"Expected {n} desired poles, got {len(poles)}.")
    return np.array(poles, dtype=complex)

def load_json_ABC(path: str):
    with open(path, "r", encoding="utf-8") as f:
        jd = json.load(f)
    A = np.array(jd["A"], dtype=complex)
    B = np.array(jd["B"], dtype=complex)
    C = np.array(jd["C"], dtype=complex)
    return A, B, C

def safe_scalar(x: Any) -> Any:
    if isinstance(x, (int, float, str, bool)):
        return x
    if isinstance(x, complex):
        return float(x.real) if abs(x.imag) < 1e-12 else f"{x.real}+{x.imag}j"
    if isinstance(x, np.generic):
        return safe_scalar(x.item())
    return str(x)

def safeify(obj: Any) -> Any:
    if obj is None:
        return None
    import numpy as np
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, complex):
        return safe_scalar(obj)
    if isinstance(obj, np.ndarray):
        return [safeify(v) for v in obj.tolist()]
    if isinstance(obj, (list, tuple)):
        return [safeify(v) for v in obj]
    if isinstance(obj, dict):
        return {str(k): safeify(v) for k, v in obj.items()}
    if isinstance(obj, Path):
        return str(obj)
    return str(obj)
