from __future__ import annotations
import os
from functools import wraps

# Package-scoped I/O roots
PKG_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
IN_DIR  = os.path.join(PKG_ROOT, "in")
OUT_DIR = os.path.join(PKG_ROOT, "out")

def ensure_pkg_out_dir(path: str | None) -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    if path is None:
        return OUT_DIR
    base = os.path.basename(path)
    return os.path.join(OUT_DIR, base)

def in_pkg_path(*parts: str) -> str:
    return os.path.join(IN_DIR, *parts)

def out_pkg_path(*parts: str) -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    return os.path.join(OUT_DIR, *parts)

def with_out_dir(func):
    # Decorator to rewrite any filename output argument into the package out/ dir.
    # Expects the wrapped function to accept an output path as first argument.
    @wraps(func)
    def wrapper(path, *args, **kwargs):
        remapped = ensure_pkg_out_dir(path)
        return func(remapped, *args, **kwargs)
    return wrapper
