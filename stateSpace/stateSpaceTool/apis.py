
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass(frozen=True)
class RunRequest:
    # Inputs
    form: str = "auto"                # auto|zmin1|z|expr|zpk
    num: Optional[str] = None
    den: Optional[str] = None
    zeros: Optional[str] = None
    poles: Optional[str] = None
    gain: Optional[float] = None

    # Which realizations to produce
    forms: str = "cont,obs,diag,jordan"

    # Options
    realblocks: bool = False          # convert simple complex conj pairs to real 2x2 blocks
    dt: float = 1.0                   # sample time for python-control check
    latex: bool = False
    latex_out: Optional[str] = None
    json_out: Optional[str] = None
    check: str = "brief"              # off|brief|full
    quiet: bool = False

@dataclass
class RunResult:
    # JSON-able realizations by key -> dict of A,B,C,D
    realizations: Dict[str, Dict[str, List[List[float]]]]
    latex: Optional[str] = None
    check_log: Optional[str] = None
