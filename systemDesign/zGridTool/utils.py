# -*- coding: utf-8 -*-
"""
Utilities and decorators for systemDesign.zGridTool.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable, Any, TypeVar
import functools
import logging
import os

ROOT = Path(__file__).resolve().parent
IN_DIR  = ROOT / "in"
OUT_DIR = ROOT / "out"
IN_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

def ensure_out_path(name: Optional[str]) -> Optional[Path]:
    if name is None:
        return None
    p = Path(name)
    return p if p.is_absolute() else (OUT_DIR / p)

def ensure_in_path(name: str) -> Path:
    p = Path(name)
    return p if p.is_absolute() else (IN_DIR / p)

F = TypeVar("F", bound=Callable[..., Any])

def log_call(fn: F) -> F:
    """Simple decorator that logs call entry/exit for debugging/test visibility."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        logging.getLogger(__name__).debug("→ %s args=%s kwargs=%s", fn.__name__, args[1:] if args else (), kwargs)
        res = fn(*args, **kwargs)
        logging.getLogger(__name__).debug("← %s -> %s", fn.__name__, type(res).__name__ if res is not None else None)
        return res
    return wrapper  # type: ignore[return-value]
