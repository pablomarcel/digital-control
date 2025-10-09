from __future__ import annotations
import os, functools, time
from typing import Callable, Any

PKG_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
IN_DIR   = os.path.join(PKG_ROOT, "in")
OUT_DIR  = os.path.join(PKG_ROOT, "out")

def out_path(path: str | None) -> str | None:
    if not path:
        return None
    if os.path.basename(path) == path:
        return os.path.join(OUT_DIR, path)
    return path

def timed(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.time()
        res = func(*args, **kwargs)
        dt = time.time() - t0
        try:
            setattr(res, "_elapsed_s", dt)
        except Exception:
            pass
        return res
    return wrapper
