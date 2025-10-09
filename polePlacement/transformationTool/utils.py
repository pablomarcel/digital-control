
from __future__ import annotations
import functools, os, json
from typing import Any
import numpy as np

OUTDIR = os.path.join(os.path.dirname(__file__), "out")

def ensure_outdir():
    os.makedirs(OUTDIR, exist_ok=True)
    return OUTDIR

def numpy_json(obj: Any) -> Any:
    if isinstance(obj, np.ndarray):
        return [numpy_json(x) for x in obj.tolist()]
    if isinstance(obj, (np.generic,)):
        return numpy_json(obj.item())
    if isinstance(obj, complex):
        if abs(obj.imag) < 1e-14:
            return float(obj.real)
        return {"re": float(obj.real), "im": float(obj.imag)}
    if isinstance(obj, (list, tuple)):
        return [numpy_json(x) for x in obj]
    if isinstance(obj, dict):
        return {k: numpy_json(v) for k, v in obj.items()}
    return obj

def pretty_mat(M: np.ndarray, w: int = 12, p: int = 6) -> str:
    if M is None:
        return "(none)"
    out = []
    for r in M:
        row = []
        for v in r:
            if abs(getattr(v, "imag", 0.0)) < 1e-14:
                row.append(f"{float(getattr(v,'real',v)):{w}.{p}f}")
            else:
                row.append(f"{complex(v):{w}.{p}g}")
        out.append(" ".join(row))
    return "\n".join(out)

def dump_json(obj: dict, basename: str):
    ensure_outdir()
    path = os.path.join(OUTDIR, f"{basename}.json")
    with open(path, "w") as f:
        json.dump(numpy_json(obj), f, indent=2)

def save_csv_matrix(M: np.ndarray, path: str):
    import csv
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        for r in M:
            w.writerow([complex(x) for x in r])

def save_csv_bundle(mats: dict, basename: str):
    ensure_outdir()
    for key, M in mats.items():
        if M is None:
            continue
        save_csv_matrix(M, os.path.join(OUTDIR, f"{basename}_{key}.csv"))

def cached(fn):
    """Simple memoization decorator for pure helpers."""
    cache = {}
    @functools.wraps(fn)
    def wrapper(*args):
        if args in cache:
            return cache[args]
        res = fn(*args)
        cache[args] = res
        return res
    return wrapper
