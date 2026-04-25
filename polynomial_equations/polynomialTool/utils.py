# -*- coding: utf-8 -*-
"""Utility helpers for :mod:`polynomial_equations.polynomialTool`.

This module intentionally keeps its docstrings conservative for Sphinx and
GitHub Pages builds. The helpers centralize package-local input and output
path handling plus a tiny optional call logger used during debugging.
"""
from __future__ import annotations

import os
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, cast


# Package-local roots used to anchor relative paths such as ``in/example.json``
# and ``out/results.json``.
PKG_DIR = os.path.dirname(__file__)
IN_DIR = os.path.join(PKG_DIR, "in")
OUT_DIR = os.path.join(PKG_DIR, "out")

_F = TypeVar("_F", bound=Callable[..., Any])


def ensure_dir_for(path: Optional[str]) -> None:
    """Create the parent directory for ``path`` when one is present.

    Passing ``None`` or a bare filename is a no-op. Absolute and relative
    filenames with a directory component are both supported.
    """
    if not path:
        return

    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)


def in_path(*parts: str) -> str:
    """Return a path under the package input directory.

    The parent directory for the returned path is created before returning the
    path string. This keeps callers simple when they need to read or create
    files under the package-local ``in`` folder.
    """
    path = os.path.join(IN_DIR, *parts)
    ensure_dir_for(path)
    return path


def out_path(*parts: str) -> str:
    """Return a path under the package output directory.

    The parent directory for the returned path is created before returning the
    path string. This keeps exports anchored to the package-local ``out``
    folder when the user supplies an output path that starts with ``out``.
    """
    path = os.path.join(OUT_DIR, *parts)
    ensure_dir_for(path)
    return path


def _strip_leading_folder(path: str, folder: str) -> str:
    """Remove a leading package folder prefix from ``path`` when present.

    The accepted prefixes are ``folder`` followed by the platform separator and
    ``./folder`` followed by the platform separator. Paths that do not use one
    of those prefixes are returned unchanged.
    """
    prefix = folder + os.sep
    if path.startswith(prefix):
        return path[len(prefix) :]

    dot_prefix = "." + os.sep + folder + os.sep
    if path.startswith(dot_prefix):
        return path[len(dot_prefix) :]

    return path


def resolve_in(path: Optional[str]) -> Optional[str]:
    """Resolve a user-supplied input path.

    Absolute paths are returned unchanged. Relative paths that start with the
    package input folder name are anchored under ``IN_DIR``. Other relative
    paths are left unchanged so callers may intentionally use the current
    working directory.
    """
    if not path:
        return path

    if os.path.isabs(path):
        return path

    subpath = _strip_leading_folder(path, "in")
    if subpath != path:
        return in_path(subpath)

    return path


def resolve_out(path: Optional[str]) -> Optional[str]:
    """Resolve a user-supplied output path.

    Absolute paths are returned after their parent directory is created.
    Relative paths that start with the package output folder name are anchored
    under ``OUT_DIR``. Other relative paths are left unchanged, but their parent
    directory is still created when applicable.
    """
    if not path:
        return path

    if os.path.isabs(path):
        ensure_dir_for(path)
        return path

    subpath = _strip_leading_folder(path, "out")
    if subpath != path:
        return out_path(subpath)

    ensure_dir_for(path)
    return path


def log_call(fn: _F) -> _F:
    """Return a decorator wrapper that prints a compact call trace.

    By default, the wrapper prints only the wrapped function name. Set the
    ``POLY_LOG_CALLS`` environment variable to ``1`` to include positional and
    keyword argument values in the printed trace. The wrapped function return
    value is passed through unchanged.
    """

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        verbose = os.environ.get("POLY_LOG_CALLS", "0") == "1"
        if verbose:
            print(f"[{fn.__name__}] called with args={args}, kwargs={kwargs}.")
        else:
            print(f"[{fn.__name__}] called.")
        return fn(*args, **kwargs)

    return cast(_F, wrapper)


__all__ = [
    "PKG_DIR",
    "IN_DIR",
    "OUT_DIR",
    "ensure_dir_for",
    "in_path",
    "out_path",
    "resolve_in",
    "resolve_out",
    "log_call",
]
