from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any, List

import numpy as np
import yaml


def parse_matrix(s: str | list | tuple | np.ndarray) -> np.ndarray:
    """
    Parse a matrix from CLI/YAML.
    Accepts:
      - string with semicolons/commas: "1 2; 3 4" or "[[1,2],[3,4]]"
      - list-of-lists, list, tuple
      - numpy.ndarray
      - "1;2;3" (col vec) | "1 2 3" (row vec)
    Always returns 2-D float ndarray.
    """
    if s is None:
        raise ValueError("matrix argument is None")
    # numpy arrays pass-through
    if isinstance(s, np.ndarray):
        arr = np.array(s, dtype=float)
        return np.atleast_2d(arr)
    if isinstance(s, (list, tuple)):
        arr = np.array(s, dtype=float)
        return np.atleast_2d(arr)
    s = str(s).strip()
    if s.startswith("["):
        try:
            arr = np.array(ast.literal_eval(s), dtype=float)
        except Exception:
            # fallback: convert '[[1 2],[3 4]]' -> '[[1,2],[3,4]]'
            s2 = re.sub(r'(?<=\d)\s+(?=\d)', ',', s)
            arr = np.array(ast.literal_eval(s2), dtype=float)
    else:
        rows = [r for r in (x.strip() for x in s.split(";")) if r]
        data = []
        for r in rows:
            tokens = [t for t in r.replace(",", " ").split() if t]
            vals: List[complex] = []
            for t in tokens:
                t = t.replace("i", "j")
                vals.append(complex(t))
            data.append(vals)
        maxlen = max(len(r) for r in data) if data else 0
        for r in data:
            if len(r) < maxlen:
                r += [0] * (maxlen - len(r))
        arr = np.array(data, dtype=complex)
        if np.all(np.isreal(arr)):
            arr = arr.real
    arr = np.atleast_2d(arr)
    return arr.astype(float)


def parse_poles(s: str | list) -> List[complex]:
    if isinstance(s, list):
        return [complex(str(it).replace("i", "j")) for it in s]
    items = [w for w in str(s).replace(" ", "").split(",") if w]
    return [complex(it.replace("i", "j")) for it in items]


def load_yaml(path: str | Path) -> dict:
    with Path(path).open("r") as f:
        return yaml.safe_load(f)


def maybe_json(v: Any) -> Any:
    """If v looks like JSON text, return parsed, else v unchanged."""
    if isinstance(v, str) and (v.strip().startswith("[") or v.strip().startswith("{")):
        try:
            return json.loads(v)
        except Exception:
            return v
    return v
