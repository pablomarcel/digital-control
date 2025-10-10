
from __future__ import annotations
from typing import Callable, Any
import time
import os

def timeit(func: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        res = func(*args, **kwargs)
        dt = time.perf_counter() - t0
        return res
    return wrapper

def out_path(pkg_dir: str, *parts: str) -> str:
    """Resolve an output path under this package's out/ directory."""
    outdir = os.path.join(pkg_dir, "out")
    os.makedirs(outdir, exist_ok=True)
    return os.path.join(outdir, *parts)
