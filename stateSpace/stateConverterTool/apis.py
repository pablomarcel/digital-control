from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import sympy as sp

@dataclass(frozen=True)
class RunRequest:
    # Inputs (either explicit matrices or example name)
    A: Optional[sp.Matrix] = None
    B: Optional[sp.Matrix] = None
    C: Optional[sp.Matrix] = None
    D: Optional[sp.Matrix] = None
    T: Optional[sp.Expr] = None

    example: Optional[str] = None  # 'ogata_5_4' | 'ogata_5_5' | 'matlab_p318'

    # Options
    digits: int = 6
    evalf: Optional[int] = None
    simplify: bool = True
    force_inverse: bool = False
    allow_singular_fallback: bool = True
    want_latex: bool = False
    latex_out: Optional[str] = None


@dataclass
class RunResult:
    G: sp.Matrix
    H: sp.Matrix
    F: sp.Matrix
    Finv: Optional[sp.Matrix]  # (zI-G)^(-1) if computed
    latex: Optional[str] = None
