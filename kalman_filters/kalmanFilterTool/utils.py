from __future__ import annotations
import os
from typing import Callable, Any
import functools, time

def ensure_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def out_path(out_dir: str, name: str | None, default_name: str) -> str:
    base = os.path.basename(name) if name else default_name
    if name and (os.path.isabs(name) or os.path.dirname(name)):
        ensure_dir(name)
        return name
    p = os.path.join(out_dir, base)
    ensure_dir(p)
    return p

def timing(fn: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        res = fn(*args, **kwargs)
        _ = time.perf_counter() - t0
        return res
    return wrapper
