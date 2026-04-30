#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Utility helpers for the model_predictive_control package."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
import json
import math
import os
import sys

import numpy as np


PACKAGE_NAME = "model_predictive_control"


class MPCError(RuntimeError):
    """Base exception for package-level MPC errors."""


class InputError(MPCError):
    """Raised when an input file or specification is invalid."""


@dataclass(frozen=True)
class ProjectPaths:
    """Resolved paths used by the command-line application."""

    package_dir: Path
    in_dir: Path
    out_dir: Path


def package_dir() -> Path:
    """Return the directory that contains this package."""

    return Path(__file__).resolve().parent


def resolve_project_paths(out_dir: str | Path | None = None) -> ProjectPaths:
    """Resolve package input and output folders.

    Parameters
    ----------
    out_dir:
        Optional output directory. If omitted, the package-level ``out``
        directory is used.
    """

    root = package_dir()
    in_dir = root / "in"
    resolved_out = Path(out_dir).expanduser().resolve() if out_dir else root / "out"
    in_dir.mkdir(parents=True, exist_ok=True)
    resolved_out.mkdir(parents=True, exist_ok=True)
    return ProjectPaths(package_dir=root, in_dir=in_dir, out_dir=resolved_out)


def resolve_input_path(path_or_name: str | Path) -> Path:
    """Resolve an input path from several common working directories.

    The resolver supports commands launched from the repository root, from the
    package directory, or directly from a ``RUNS.md`` fenced command block.
    """

    candidate = Path(path_or_name).expanduser()
    if candidate.is_file():
        return candidate.resolve()

    root = package_dir()
    search_candidates = [
        Path.cwd() / candidate,
        root / candidate,
        root / "in" / candidate,
        root / "in" / candidate.name,
        Path.cwd() / "in" / candidate.name,
        Path.cwd() / PACKAGE_NAME / "in" / candidate.name,
    ]
    for item in search_candidates:
        if item.is_file():
            return item.resolve()

    raise FileNotFoundError(
        f"Could not find input file {path_or_name!r}. Tried cwd, package root, "
        "package/in, cwd/in, and cwd/model_predictive_control/in."
    )


def load_json(path: str | Path) -> dict[str, Any]:
    """Load a JSON object from disk."""

    resolved = resolve_input_path(path)
    with resolved.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise InputError(f"Input JSON must contain an object at top level: {resolved}")
    return data


def save_json(data: dict[str, Any], path: str | Path) -> Path:
    """Save a dictionary as pretty JSON."""

    resolved = Path(path).expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("w", encoding="utf-8") as f:
        json.dump(to_jsonable(data), f, indent=2, sort_keys=False)
        f.write("\n")
    return resolved


def to_jsonable(value: Any) -> Any:
    """Convert NumPy-heavy objects into JSON-serializable values."""

    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, Path):
        return str(value)
    return value


def as_array(value: Any, name: str, *, ndim: int | None = None) -> np.ndarray:
    """Coerce a value to a finite NumPy array."""

    arr = np.asarray(value, dtype=float)
    if ndim is not None and arr.ndim != ndim:
        raise InputError(f"{name} must have {ndim} dimensions; got shape {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise InputError(f"{name} contains non-finite values")
    return arr


def as_square_matrix(value: Any, name: str) -> np.ndarray:
    """Coerce a value to a finite square matrix."""

    arr = as_array(value, name, ndim=2)
    if arr.shape[0] != arr.shape[1]:
        raise InputError(f"{name} must be square; got shape {arr.shape}")
    return arr


def vector_or_default(value: Any, default: float, length: int, name: str) -> np.ndarray:
    """Return a vector of a requested length from scalar, list, or None."""

    if value is None:
        return np.full(length, float(default))
    arr = np.asarray(value, dtype=float)
    if arr.ndim == 0:
        return np.full(length, float(arr))
    if arr.shape != (length,):
        raise InputError(f"{name} must be scalar or length {length}; got shape {arr.shape}")
    return arr


def matrix_weight(value: Any, size: int, name: str, default_diag: float = 1.0) -> np.ndarray:
    """Build a positive semidefinite weight matrix from scalar, vector, or matrix."""

    if value is None:
        return np.eye(size) * float(default_diag)
    arr = np.asarray(value, dtype=float)
    if arr.ndim == 0:
        return np.eye(size) * float(arr)
    if arr.ndim == 1:
        if arr.size != size:
            raise InputError(f"{name} vector must have length {size}; got {arr.size}")
        return np.diag(arr)
    if arr.shape != (size, size):
        raise InputError(f"{name} matrix must have shape {(size, size)}; got {arr.shape}")
    return arr


def broadcast_reference(value: Any, steps: int, size: int, name: str) -> np.ndarray:
    """Broadcast a reference or disturbance trajectory to ``steps`` rows."""

    if value is None:
        return np.zeros((steps, size))
    arr = np.asarray(value, dtype=float)
    if arr.ndim == 0:
        return np.full((steps, size), float(arr))
    if arr.ndim == 1:
        if arr.size != size:
            raise InputError(f"{name} vector must have length {size}; got {arr.size}")
        return np.repeat(arr.reshape(1, -1), steps, axis=0)
    if arr.ndim == 2:
        if arr.shape[1] != size:
            raise InputError(f"{name} must have {size} columns; got shape {arr.shape}")
        if arr.shape[0] >= steps:
            return arr[:steps].copy()
        last = np.repeat(arr[-1:].copy(), steps - arr.shape[0], axis=0)
        return np.vstack([arr, last])
    raise InputError(f"{name} must be scalar, vector, or 2-D trajectory")


def clip_with_none(value: np.ndarray, lo: np.ndarray | None, hi: np.ndarray | None) -> np.ndarray:
    """Clip an array while allowing missing lower or upper bounds."""

    out = np.asarray(value, dtype=float).copy()
    if lo is not None:
        out = np.maximum(out, lo)
    if hi is not None:
        out = np.minimum(out, hi)
    return out


def safe_slug(text: str) -> str:
    """Create a simple filesystem-safe slug."""

    allowed = []
    for char in str(text).strip().lower():
        if char.isalnum():
            allowed.append(char)
        elif char in {" ", "-", "_", "."}:
            allowed.append("_")
    slug = "".join(allowed).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "mpc_run"


def print_kv(rows: Iterable[tuple[str, Any]]) -> None:
    """Print aligned key-value rows to stdout."""

    rows = list(rows)
    if not rows:
        return
    width = max(len(str(k)) for k, _ in rows)
    for key, value in rows:
        print(f"{key:<{width}} : {value}")


def optional_import(module_name: str) -> tuple[bool, str]:
    """Return whether a module is importable and a compact status message."""

    try:
        __import__(module_name)
    except Exception as exc:  # pragma: no cover - diagnostic helper
        return False, f"{module_name}: not available ({exc.__class__.__name__})"
    return True, f"{module_name}: available"
