
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DesignRequest:
    kind: str                     # "prediction" | "current" | "dlqe" | "min"
    A: str | list
    C: str | list
    poles: Optional[str | list] = None
    B: Optional[str | list] = None
    method: str = "place"
    # dlqe
    G: Optional[str | list] = None
    Qn: Optional[str | list] = None
    Rn: Optional[str | list] = None
    # exports
    csv: Optional[str] = None
    out: Optional[str] = None
    # config
    config: Optional[str] = None


@dataclass
class ClosedLoopRequest:
    A: str | list
    B: str | list
    C: str | list
    K: str | list
    L: str | list
    out: Optional[str] = None
    config: Optional[str] = None


@dataclass
class K0Request:
    A: str | list
    B: str | list
    C: str | list
    K: str | list
    L: Optional[str | list] = None
    mode: str = "state"           # "state" | "ogata"
    ogata_extra_gain: Optional[float] = None
    out: Optional[str] = None
    config: Optional[str] = None


@dataclass
class SelectRequest:
    A: str | list
    B: str | list
    C: str | list
    K: str | list
    method: str = "place"
    rule_of_thumb: Optional[str] = None     # comma plant poles
    speedup: float = 5.0
    sweep: Optional[str] = None             # "0.2,0.2; 0.4+0.4j,0.4-0.4j"
    steps: int = 200
    dlqe: bool = False
    G: Optional[str | list] = None
    Qn: Optional[str | list] = None
    Rn: Optional[str | list] = None
    csv: Optional[str] = None
    out: Optional[str] = None
    config: Optional[str] = None


@dataclass
class SimRequest:
    A: str | list
    B: str | list
    C: str | list
    K: str | list
    L: str | list
    N: int = 60
    Ts: float = 1.0
    ref: str = "step"             # none|step|ramp
    K0: Optional[str] = None      # 'auto' | float string | None
    k0_mode: str = "state"        # state|ogata
    ogata_extra_gain: Optional[float] = None
    csv: Optional[str] = None
    out: Optional[str] = None
    plot: bool = False
    plot_type: str = "points"
    plotly: bool = False
    html: Optional[str] = None
    config: Optional[str] = None


@dataclass
class ExampleRequest:
    which: str                 # 6-9 | 6-10 | 6-11 | 6-12
    Ts: float = 0.2
