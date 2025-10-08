
from __future__ import annotations
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import Callable, Any, Dict, Optional, List, Tuple

import sympy as sp

ROOT = Path(__file__).resolve().parent
IN_DIR  = ROOT / "in"
OUT_DIR = ROOT / "out"
IN_DIR.mkdir(exist_ok=True, parents=True)
OUT_DIR.mkdir(exist_ok=True, parents=True)

def in_path(name: str) -> Path:
    p = Path(name)
    return p if p.is_absolute() else (IN_DIR / p)

def out_path(name: str) -> Path:
    p = Path(name)
    return p if p.is_absolute() else (OUT_DIR / p)

# -------------------- formatting helpers --------------------

def sstr(x) -> str:
    if isinstance(x, (int,)) or isinstance(x, sp.Integer):
        return str(int(x))
    if isinstance(x, (float,)) or isinstance(x, sp.Float):
        return f"{float(x):.6g}"
    try:
        xn = sp.nsimplify(x)
        if xn.is_Number:
            return f"{float(xn):.6g}"
    except Exception:
        pass
    return sp.sstr(x)

def fmt_vec(vec: List[sp.Expr]) -> str:
    return "  ".join(sstr(v) for v in vec)

def fmt_row(label: str, vec: List[sp.Expr], width: int=12) -> str:
    return f"{label:<{width}}" + fmt_vec(vec)

def banner(title: str) -> str:
    return "\n" + title + "\n" + "-" * 78 + "\n"

# -------------------- small decorators --------------------

def ensure_numeric_tols(fn: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(fn)
    def wrapper(*args, **kwargs):
        for key in ("abs_tol", "rel_tol", "unit_tol"):
            if key in kwargs and kwargs[key] is not None:
                kwargs[key] = float(kwargs[key])
        return fn(*args, **kwargs)
    return wrapper

def dataclass_repr(cls):
    """Prettier __repr__ for dataclasses (field=value, ...)."""
    def __repr__(self):
        fields = ", ".join(f"{k}={getattr(self, k)!r}" for k in self.__dataclass_fields__.keys())
        return f"{cls.__name__}({fields})"
    cls.__repr__ = __repr__
    return cls
