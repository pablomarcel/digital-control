
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Literal

from .utils import dataclass_repr

Method = Literal["jury","schur","bilinear","all"]

@dataclass_repr
@dataclass
class RunRequest:
    # Source (one of the two must be provided by the CLI/app)
    coeffs: Optional[str] = None        # "1, -1.2, 0.07, 0.3, -0.08" (high->const)
    json_in: Optional[str] = None       # Relative to in/
    # Options
    method: Method = "jury"
    solve_range: bool = False
    eval_K: Optional[float] = None
    T: Optional[float] = None
    rational: bool = False
    abs_tol: float = 1e-10
    rel_tol: float = 1e-9
    unit_tol: float = 2e-6
    save_table: Optional[str] = None    # relative to out/
    save_json: Optional[str] = None     # relative to out/

@dataclass_repr
@dataclass
class MethodResult:
    verdict: str
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass_repr
@dataclass
class RunResult:
    order: int
    polynomial: str
    coeffs_high_to_const: List[str]
    parameter: Optional[str]
    methods: Dict[str, MethodResult]
    eval_summary: Optional[Dict[str, Any]] = None
