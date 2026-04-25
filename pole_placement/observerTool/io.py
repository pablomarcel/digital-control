from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any, List

import numpy as np
import yaml


def parse_matrix(s: str | list | tuple | np.ndarray) -> np.ndarray:
    """Parse a matrix-like value from CLI, JSON, YAML, or Python objects.

    Supported inputs include strings such as ``"1 2; 3 4"``,
    Python-style nested lists such as ``"[[1, 2], [3, 4]]"``,
    one-dimensional row or column vector strings, Python lists/tuples, and
    ``numpy.ndarray`` values.

    The return value is always at least two-dimensional. Real-valued complex
    inputs are reduced to real arrays when possible. The final return type is a
    floating-point ``numpy.ndarray`` because the observer workflows expect real
    state-space matrices.
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

    text = str(s).strip()
    if not text:
        raise ValueError("matrix argument is empty")

    if text.startswith("["):
        try:
            arr = np.array(ast.literal_eval(text), dtype=float)
        except Exception:
            # Fallback for forms such as '[[1 2], [3 4]]'.
            text2 = re.sub(r"(?<=\d)\s+(?=\d)", ",", text)
            arr = np.array(ast.literal_eval(text2), dtype=float)
    else:
        rows = [row for row in (part.strip() for part in text.split(";")) if row]
        data: list[list[complex]] = []

        for row in rows:
            tokens = [token for token in row.replace(",", " ").split() if token]
            vals: List[complex] = []
            for token in tokens:
                vals.append(complex(token.replace("i", "j")))
            data.append(vals)

        if not data:
            raise ValueError("matrix argument did not contain numeric data")

        maxlen = max(len(row) for row in data)
        if maxlen == 0:
            raise ValueError("matrix argument did not contain numeric data")

        for row in data:
            if len(row) < maxlen:
                row += [0] * (maxlen - len(row))

        arr = np.array(data, dtype=complex)
        if np.all(np.isreal(arr)):
            arr = arr.real

    arr = np.atleast_2d(arr)
    return arr.astype(float)


def parse_poles(s: str | list) -> List[complex]:
    """Parse a pole list from a comma-separated string or Python list.

    The parser accepts ``i`` or ``j`` as the imaginary-unit suffix. For example,
    ``"0.5+0.5j,0.5-0.5j"`` and ``"0.5+0.5i,0.5-0.5i"`` are both valid.
    """
    if isinstance(s, list):
        return [complex(str(item).replace("i", "j")) for item in s]

    items = [item for item in str(s).replace(" ", "").split(",") if item]
    return [complex(item.replace("i", "j")) for item in items]


def load_yaml(path: str | Path) -> dict:
    """Load a YAML file and return its top-level mapping.

    Parameters
    ----------
    path:
        File path to read.
    """
    with Path(path).open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML file must contain a mapping at the top level: {path}")
    return data


def maybe_json(v: Any) -> Any:
    """Return parsed JSON when ``v`` looks like JSON text.

    Non-string values are returned unchanged. Strings that do not start with
    ``[`` or ``{`` are also returned unchanged. If JSON parsing fails, the
    original value is returned.
    """
    if isinstance(v, str) and (v.strip().startswith("[") or v.strip().startswith("{")):
        try:
            return json.loads(v)
        except Exception:
            return v
    return v
