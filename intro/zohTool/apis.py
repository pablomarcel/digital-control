from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class RunRequest:
    """Typed input for running a ZOH simulation."""
    # Source (exactly one of these should be provided by CLI; app validates):
    csv: Optional[str] = None
    json_spec: Optional[str] = None

    # Core parameters
    Ts: float = 1e-3
    delay: float = 0.0
    droop_tau: float = float('inf')
    offset: float = 0.0

    # Units for logs/exports
    units: str = "V"

    # VCD scaling
    scale: float = 1e6
    idx_bits: Optional[int] = None

    # I/O directories (used by CLI to resolve relative filenames)
    in_dir: str = "in"
    out_dir: str = "out"

    # Optional outputs
    out_csv: Optional[str] = None
    out_vcd: Optional[str] = None

@dataclass
class IntervalEvent:
    k: int
    t0: float
    t1: float
    u_in: float
    y0: float
    y1: float

    def as_dict(self) -> Dict[str, Any]:
        return {"k": self.k, "t0": self.t0, "t1": self.t1, "u_in": self.u_in, "y0": self.y0, "y1": self.y1}

@dataclass
class RunResult:
    events: List[IntervalEvent] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)
    wrote_csv: Optional[str] = None
    wrote_vcd: Optional[str] = None
