from __future__ import annotations
import os
from functools import wraps
PKG_DIR = os.path.dirname(__file__)
IN_DIR  = os.path.join(PKG_DIR, "in")
OUT_DIR = os.path.join(PKG_DIR, "out")
def ensure_dir_for(path):
    if path and os.path.dirname(path): os.makedirs(os.path.dirname(path), exist_ok=True)
def in_path(*parts): return os.path.join(IN_DIR, *parts)
def out_path(*parts):
    p = os.path.join(OUT_DIR, *parts); ensure_dir_for(p); return p
def log_call(fn):
    from functools import wraps
    @wraps(fn)
    def w(*a, **k): print(f"[{fn.__name__}] called."); return fn(*a, **k)
    return w
