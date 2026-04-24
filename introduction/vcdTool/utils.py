from __future__ import annotations
import functools, time, os
from typing import Callable, Any

def timed(fn: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.time()
        out = fn(*args, **kwargs)
        dt = (time.time() - t0)*1000.0
        print(f"[timed] {fn.__name__} took {dt:.1f} ms")
        return out
    return wrapper

def ensure_dir_for_file(path: str | None) -> None:
    if not path:
        return
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
