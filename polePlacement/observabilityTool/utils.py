
from __future__ import annotations
import os, functools, time
from typing import Callable

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def pkg_outdir() -> str:
    # Always write relative to the package (./out)
    here = os.path.dirname(__file__)
    out = os.path.join(here, "out")
    ensure_dir(out)
    return out

def timed(fn: Callable):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.time()
        out = fn(*args, **kwargs)
        dt = time.time() - t0
        return out
    return wrapper
