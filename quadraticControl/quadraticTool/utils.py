# utils.py
from __future__ import annotations

import os
import time
import functools
import logging
from typing import Callable, Any, Tuple, Dict, List, Union

import numpy as np

__all__ = [
    "PKG_DIR", "IN_DIR", "OUT_DIR",
    "ensure_dir", "pkg_path", "in_path", "out_path",
    "timeit", "setup_logging",
    "np_to_native", "native_to_np",
]

# --------------------------------------------------------------------------------------
# Package paths
# --------------------------------------------------------------------------------------
PKG_DIR = os.path.abspath(os.path.dirname(__file__))
IN_DIR  = os.path.join(PKG_DIR, "in")
OUT_DIR = os.path.join(PKG_DIR, "out")


def ensure_dir(d: str) -> None:
    """Create directory if it doesn't exist."""
    os.makedirs(d, exist_ok=True)


def pkg_path(*parts: str) -> str:
    """Path relative to the package directory."""
    return os.path.join(PKG_DIR, *parts)


def in_path(*parts: str) -> str:
    """Path inside the 'in' directory."""
    return os.path.join(IN_DIR, *parts)


def out_path(*parts: str) -> str:
    """Path inside the 'out' directory."""
    return os.path.join(OUT_DIR, *parts)


# --------------------------------------------------------------------------------------
# Timing / logging
# --------------------------------------------------------------------------------------
def timeit(fn: Callable[..., Any]) -> Callable[..., Tuple[Any, float]]:
    """
    Decorator that returns (result, elapsed_seconds).

    Example:
        @timeit
        def work(x):
            ...
            return y

        (y, dt) = work(3)
    """
    @functools.wraps(fn)
    def _wrap(*args, **kwargs) -> Tuple[Any, float]:
        t0 = time.perf_counter()
        res = fn(*args, **kwargs)
        dt = time.perf_counter() - t0
        return res, dt
    return _wrap


def setup_logging(level: str = "INFO") -> None:
    """Initialize basic logging with a simple, readable format."""
    lvl = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=lvl,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


# --------------------------------------------------------------------------------------
# Numpy <-> JSON-friendly serialization helpers
# --------------------------------------------------------------------------------------
_JSONScalar = Union[str, int, float, bool, None]


def np_to_native(x: Any) -> Any:
    """
    Convert numpy arrays/scalars to JSON-friendly Python types.

    - np.ndarray -> {"__ndarray__": <nested lists>}
    - numpy scalars -> Python scalars via .item()
    - Containers (list/tuple/dict) handled recursively.
    - Other types are returned unchanged.
    """
    if isinstance(x, np.ndarray):
        return {"__ndarray__": x.tolist()}
    if isinstance(x, np.generic):  # numpy scalar (int64, float64, etc.)
        return x.item()
    if isinstance(x, (list, tuple)):
        return [np_to_native(v) for v in x]
    if isinstance(x, dict):
        return {k: np_to_native(v) for k, v in x.items()}
    return x


def native_to_np(x: Any) -> Any:
    """
    Inverse of np_to_native.

    - {"__ndarray__": <nested lists>} -> np.array(dtype=float)
    - Recurses into containers; leaves plain scalars as-is.
    """
    if isinstance(x, dict) and "__ndarray__" in x:
        return np.asarray(x["__ndarray__"], dtype=float)
    if isinstance(x, list):
        return [native_to_np(v) for v in x]
    if isinstance(x, dict):
        return {k: native_to_np(v) for k, v in x.items()}
    return x
