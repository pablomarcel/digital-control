from __future__ import annotations
import os
from typing import Callable, Any
from functools import wraps

# ------------------------- Paths & Directories -------------------------

def ensure_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def looks_inline_json(s: str) -> bool:
    if s is None:
        return False
    t = s.strip()
    return (t.startswith('[') or t.startswith('{'))

def resolve_input_path(p: str | None, in_dir: str) -> str | None:
    """Resolve an input path: if inline JSON, return as-is; else search under in_dir."""
    if p is None:
        return None
    if looks_inline_json(p):
        return p
    if os.path.isabs(p) or os.path.exists(p):
        return p
    cand = os.path.join(in_dir, p)
    return cand if os.path.exists(cand) else p

def resolve_output_path(p: str | None, out_dir: str) -> str | None:
    """Resolve an output path: relative -> out_dir/relative; absolute -> as-is."""
    if p is None:
        return None
    if os.path.isabs(p) or os.path.dirname(p):
        ensure_dir(p)
        return p
    outp = os.path.join(out_dir, p)
    ensure_dir(outp)
    return outp

# ------------------------------ Decorators ------------------------------

def log_call(logger_func: Callable[[str], Any] | None = None):
    """A tiny decorator to log function calls (name + kwargs).
    Pass a logger function that accepts a single string (e.g., print).
    """
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if logger_func:
                logger_func(f"CALL {fn.__name__} args={len(args)} kwargs={kwargs}")
            return fn(*args, **kwargs)
        return wrapper
    return deco
