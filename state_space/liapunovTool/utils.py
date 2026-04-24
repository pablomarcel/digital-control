from __future__ import annotations
import functools
import time
from typing import Callable, Any

# tqdm fallback shim (so tests don't fail if tqdm missing)
try:
    from tqdm import tqdm  # type: ignore
except Exception:  # pragma: no cover
    class tqdm:  # type: ignore
        def __init__(self, total=0, desc=None): pass
        def set_postfix_str(self, s): pass
        def update(self, n=1): pass
        def __enter__(self): return self
        def __exit__(self, *exc): pass

def timed(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        res = func(*args, **kwargs)
        setattr(res, "_elapsed", time.perf_counter() - t0) if hasattr(res, "__dict__") else None
        return res
    return wrapper
