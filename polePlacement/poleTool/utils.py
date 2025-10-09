from __future__ import annotations
import functools, time, os
from pathlib import Path
import numpy as np

def ensure_out_dir(default_rel: str = "out", override: str | None = None) -> Path:
    """Return an output directory. If override is given, create and use it;
    else use ./out (package-local)."""
    p = Path(override) if override else Path(__file__).resolve().parent / default_rel
    p.mkdir(parents=True, exist_ok=True)
    return p

def timeit(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        res = func(*args, **kwargs)
        dt = (time.perf_counter() - t0) * 1000.0
        return res
    return wrapper

def to_real_if_close(M, tol: float = 1e-12):
    Mr = np.real_if_close(M, tol=tol)
    if np.all(np.isreal(Mr)):
        return Mr.real.astype(float)
    return Mr.astype(complex)

def mat_to_str(M, width: int = 11, prec: int = 6) -> str:
    import numpy as np
    M = np.array(M)
    rows = []
    for r in range(M.shape[0]):
        row = []
        for c in range(M.shape[1]):
            v = M[r, c]
            if abs(getattr(v, "imag", 0.0)) < 1e-12:
                row.append(f"{float(getattr(v,'real',v)):{width}.{prec}f}")
            else:
                row.append(f"{float(v.real):{width}.{prec}f}{v.imag:+.{prec}f}j")
        rows.append(" ".join(row))
    return "\n".join(rows)
