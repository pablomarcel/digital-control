from __future__ import annotations
import ast, os
from typing import Tuple
import sympy as sp

def parse_matrix(s: str) -> sp.Matrix:
    try:
        obj = ast.literal_eval(s)
    except Exception as e:
        raise ValueError(f"Could not parse matrix: {e}")
    if not isinstance(obj, (list, tuple)):
        raise ValueError("Matrix must be a list of lists.")
    rows = []
    for row in obj:
        if not isinstance(row, (list, tuple)):
            raise ValueError("Matrix must be a list of lists.")
        rows.append([sp.sympify(x, rational=True) for x in row])
    return sp.Matrix(rows)

def parse_scalar(s: str):
    return sp.sympify(s, rational=True)

def ensure_out_dir(p: str) -> str:
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    return p
