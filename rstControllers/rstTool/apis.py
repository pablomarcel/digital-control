
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class RunRequest:
    A: List[float]
    B: List[float]
    d: int = 0
    Ts: float = 1.0
    Acl: Optional[List[float]] = None
    poles: Optional[List[complex]] = None
    spoles: Optional[List[complex]] = None
    Ac: Optional[List[float]] = None
    Ao: Optional[List[float]] = None
    degS: Optional[int] = None
    degR: Optional[int] = None
    alloc: str = "S"
    integrator: bool = False
    Tmode: str = "unity_dc"
    T: Optional[List[float]] = None
    N: int = 200
    r_step: float = 1.0
    v_step: float = 0.0
    v_k0: int = 0
    noise_sigma: float = 0.0
    in_json: Optional[str] = None
    export_json: Optional[str] = None
    save_csv: Optional[str] = None
    pretty: bool = False

@dataclass
class RunResult:
    R: List[float]; S: List[float]; Tq: List[float]; Acl: List[float]
    y_final: float; u_final: float; sse: float
    csv_path: Optional[str]; json_path: Optional[str]
