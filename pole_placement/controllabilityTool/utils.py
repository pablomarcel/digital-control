from __future__ import annotations
import os
from functools import wraps
from typing import Any, Callable, Tuple
import numpy as np
from numpy.linalg import eig, svd

def ensure_out_dir(path: str = "out") -> None:
    os.makedirs(path, exist_ok=True)

def with_outdir(fn: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(fn)
    def _wrap(*args, **kwargs):
        ensure_out_dir(kwargs.get("outdir","out"))
        return fn(*args, **kwargs)
    return _wrap

def stable_ct(A: np.ndarray) -> bool:
    vals, _ = eig(A)
    return bool(np.all(np.real(vals) < 0.0))

def stable_dt(A: np.ndarray) -> bool:
    vals, _ = eig(A)
    return bool(np.all(np.abs(vals) < 1.0))

def rank_numeric(M: np.ndarray, tol: float | None = None) -> int:
    _, s, _ = svd(M)
    if tol is None:
        eps = np.finfo(float).eps
        tol = max(M.shape) * eps * (s[0] if s.size else 0.0)
    return int(np.sum(s > tol))

def real_if_close_for_control(X: np.ndarray) -> np.ndarray:
    Xr = np.real_if_close(X, tol=1000)
    if np.iscomplexobj(Xr):
        return X
    return Xr.astype(float)
