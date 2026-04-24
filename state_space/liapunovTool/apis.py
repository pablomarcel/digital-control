from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Literal, Dict, Any
import sympy as sp

Mode = Literal["ct", "dt", "example"]

@dataclass(frozen=True)
class RunRequest:
    mode: Mode
    # Matrices (string inputs are allowed; parsed in App/IO layer)
    A: Optional[str] = None
    G: Optional[str] = None
    Q: Optional[str] = None
    # Options
    hermitian: bool = False
    digits: int = 6
    evalf: Optional[int] = None
    latex: bool = False
    latex_out: Optional[str] = None
    # Examples
    which: Optional[str] = None  # e.g., "ogata_5_8" | "ogata_5_9"

@dataclass
class RunResult:
    mode: Mode
    hermitian: bool
    P: sp.Matrix
    pd_class: str
    latex_text: Optional[str] = None
    meta: Dict[str, Any] = None
