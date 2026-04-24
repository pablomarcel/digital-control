
from __future__ import annotations

import csv
import json
import os
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

import numpy as np


PKG_OUT = Path(__file__).resolve().parent / "out"


def ensure_dir(p: str | os.PathLike) -> Path:
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def out_path(filename: str | None) -> Path | None:
    """
    If `filename` is None -> return None.
    If `filename` is an absolute/relative path with dirs, use as-is.
    If it's just a bare filename, place it under the package ./out/.
    """
    if filename is None:
        return None
    p = Path(filename)
    if p.parent == Path("."):
        p = PKG_OUT / p.name
    return p


def save_json(path: str | os.PathLike, obj: Any) -> None:
    p = ensure_dir(path)
    with p.open("w") as f:
        f.write(asjson(obj))


def save_csv_matrix(path: str | os.PathLike, M: np.ndarray, header: Iterable[str] | None = None) -> None:
    p = ensure_dir(path)
    arr = np.array(M, dtype=float)
    with p.open("w", newline="") as f:
        w = csv.writer(f)
        if header is not None:
            w.writerow(list(header))
        if arr.ndim == 1:
            w.writerow([float(x) for x in arr])
        else:
            for r in arr:
                w.writerow([float(x) for x in np.ravel(r)])


def save_csv_series(path: str | os.PathLike, columns: Dict[str, Iterable[float]]) -> None:
    p = ensure_dir(path)
    keys = list(columns.keys())
    rows = list(zip(*[list(v) for v in columns.values()]))
    with p.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(keys)
        for r in rows:
            w.writerow(r)


def to_python_scalar(x: Any) -> Any:
    import numpy as _np
    if isinstance(x, (_np.floating,)):
        return float(x)
    if isinstance(x, (_np.integer,)):
        return int(x)
    if isinstance(x, (_np.complexfloating, complex)):
        if abs(_np.imag(x)) < 1e-12:
            return float(_np.real(x))
        return f"{_np.real(x)}{_np.imag(x):+g}j"
    if is_dataclass(x):
        return asdict(x)
    return x


def to_jsonable(obj: Any) -> Any:
    if is_dataclass(obj):
        obj = asdict(obj)
    if isinstance(obj, np.ndarray):
        return to_jsonable(obj.tolist())
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    return to_python_scalar(obj)


def asjson(obj: Any) -> str:
    return json.dumps(to_jsonable(obj), indent=2)


def eigvals_sorted(M: np.ndarray) -> List[complex]:
    vals = np.linalg.eigvals(M)
    vals = list(vals.tolist())
    vals.sort(key=lambda z: (abs(z), float(np.real(z)), float(np.imag(z))))
    return vals


def multiset_close(a: Iterable[complex], b: Iterable[complex], tol: float = 1e-8) -> bool:
    a = sorted(list(a), key=lambda z: (abs(z), float(np.real(z)), float(np.imag(z))))
    b = sorted(list(b), key=lambda z: (abs(z), float(np.real(z)), float(np.imag(z))))
    if len(a) != len(b):
        return False
    for z1, z2 in zip(a, b):
        if abs(z1 - z2) > tol:
            return False
    return True
