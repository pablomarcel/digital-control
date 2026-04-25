# utils.py
from __future__ import annotations

import functools
import logging
import os
import time
from typing import Any, Callable, Tuple, Union

import numpy as np

__all__ = [
    "PKG_DIR",
    "IN_DIR",
    "OUT_DIR",
    "ensure_dir",
    "pkg_path",
    "in_path",
    "out_path",
    "timeit",
    "setup_logging",
    "np_to_native",
    "native_to_np",
]

# --------------------------------------------------------------------------------------
# Package paths
# --------------------------------------------------------------------------------------
PKG_DIR = os.path.abspath(os.path.dirname(__file__))
IN_DIR = os.path.join(PKG_DIR, "in")
OUT_DIR = os.path.join(PKG_DIR, "out")


def ensure_dir(d: str) -> None:
    """Create a directory when it does not already exist."""
    os.makedirs(d, exist_ok=True)


def pkg_path(*parts: str) -> str:
    """Return a path relative to the package directory."""
    return os.path.join(PKG_DIR, *parts)


def in_path(*parts: str) -> str:
    """Return a path inside the package input directory."""
    return os.path.join(IN_DIR, *parts)


def out_path(*parts: str) -> str:
    """Return a path inside the package output directory."""
    return os.path.join(OUT_DIR, *parts)


# --------------------------------------------------------------------------------------
# Timing and logging
# --------------------------------------------------------------------------------------
def timeit(fn: Callable[..., Any]) -> Callable[..., Tuple[Any, float]]:
    """Return a wrapper that yields the wrapped result and elapsed seconds.

    The decorated callable returns a two-item tuple. The first item is the
    original return value from the wrapped callable. The second item is the
    elapsed wall-clock time in seconds, measured with ``time.perf_counter``.
    """

    @functools.wraps(fn)
    def _wrap(*args: Any, **kwargs: Any) -> Tuple[Any, float]:
        t0 = time.perf_counter()
        res = fn(*args, **kwargs)
        dt = time.perf_counter() - t0
        return res, dt

    return _wrap


def setup_logging(level: str = "INFO") -> None:
    """Initialize basic logging with a compact readable format."""
    lvl = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=lvl,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


# --------------------------------------------------------------------------------------
# Numpy to JSON-friendly serialization helpers
# --------------------------------------------------------------------------------------
_JSONScalar = Union[str, int, float, bool, None]


def np_to_native(x: Any) -> Any:
    """Convert NumPy objects into JSON-friendly Python values.

    Arrays are represented as dictionaries with a ``__ndarray__`` key. NumPy
    scalar values are converted with ``item``. Lists, tuples, and dictionaries
    are processed recursively. Other values are returned unchanged.
    """
    if isinstance(x, np.ndarray):
        return {"__ndarray__": x.tolist()}
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, (list, tuple)):
        return [np_to_native(v) for v in x]
    if isinstance(x, dict):
        return {k: np_to_native(v) for k, v in x.items()}
    return x


def native_to_np(x: Any) -> Any:
    """Convert JSON-friendly values produced by ``np_to_native`` back to arrays.

    Dictionaries containing a ``__ndarray__`` key are converted to NumPy arrays
    with ``dtype=float``. Lists and dictionaries are processed recursively.
    Plain scalar values are returned unchanged.
    """
    if isinstance(x, dict) and "__ndarray__" in x:
        return np.asarray(x["__ndarray__"], dtype=float)
    if isinstance(x, list):
        return [native_to_np(v) for v in x]
    if isinstance(x, dict):
        return {k: native_to_np(v) for k, v in x.items()}
    return x
