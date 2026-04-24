
from __future__ import annotations
import os, functools, time
from typing import Optional, Callable, Any

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def normalize_out_path(path: Optional[str], outdir: str) -> Optional[str]:
    if path is None:
        return None
    d = os.path.dirname(path)
    if d == "":
        ensure_dir(outdir)
        return os.path.join(outdir, path)
    ensure_dir(d)
    return path

def with_outdir_policy(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator: normalizes known output kwargs using --outdir policy."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        outdir = kwargs.get("outdir", "out")
        for key in ["matplotlib","csv","pzmap","rlocus","plotly_step","plotly_pz","plotly_rl","panel"]:
            if key in kwargs:
                kwargs[key] = normalize_out_path(kwargs.get(key), outdir)
        return func(*args, **kwargs)
    return wrapper

def timeit(label: str) -> Callable:
    def deco(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def inner(*a, **k):
            t0 = time.time()
            try:
                return fn(*a, **k)
            finally:
                dt = time.time()-t0
                print(f"[time] {label}: {dt:.3f}s")
        return inner
    return deco
