
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import sympy as sp

@dataclass
class RunRequest:
    """User-facing API for running the State Solver tool."""
    # Mode / example
    mode: str = "lti"  # "lti" or "ltv"
    example: Optional[str] = None

    # LTI
    G: Optional[str] = None
    H: Optional[str] = None
    C: Optional[str] = None
    D: Optional[str] = None
    x0: Optional[str] = None
    u: Optional[str] = None

    # LTV
    Gk: Optional[str] = None
    Hk: Optional[str] = None
    Ck: Optional[str] = None
    Dk: Optional[str] = None

    # Options
    latex: bool = False
    latex_out: Optional[str] = None
    zt: bool = False
    realblocks: bool = False
    steps: int = 6
    check: str = "brief"  # "brief" or "off"
    power_style: str = "rational"  # "rational" | "integer"

@dataclass
class MatrixBundle:
    """Structured matrices and expressions for introspection/testing."""
    G: Optional[sp.Matrix] = None
    H: Optional[sp.Matrix] = None
    C: Optional[sp.Matrix] = None
    D: Optional[sp.Matrix] = None
    x0: Optional[sp.Matrix] = None
    u_expr: Optional[sp.Expr] = None

@dataclass
class LTIResult:
    """Outputs from an LTI run."""
    matrices: MatrixBundle
    zI_minus_G: Optional[sp.Matrix] = None
    inv_zI_minus_G: Optional[sp.Matrix] = None
    det_zI_minus_G: Optional[sp.Expr] = None
    adj_zI_minus_G: Optional[sp.Matrix] = None
    leverrier_a: Optional[List[sp.Expr]] = None
    leverrier_H: Optional[List[sp.Matrix]] = None
    Psi: Optional[sp.Matrix] = None
    xk: Optional[sp.Matrix] = None
    yk: Optional[sp.Matrix] = None
    check_status: Optional[str] = None
    latex_lines: Optional[List[str]] = None

@dataclass
class LTVResult:
    """Outputs from an LTV run."""
    Phi: Optional[sp.Matrix] = None
    xs: Optional[List[sp.Matrix]] = None
    ys: Optional[List[sp.Matrix]] = None
    check_status: Optional[str] = None
    latex_lines: Optional[List[str]] = None

@dataclass
class RunResult:
    mode: str
    lti: Optional[LTIResult] = None
    ltv: Optional[LTVResult] = None
