from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

@dataclass
class RunRequest:
    mode: str
    config: Optional[str] = None
    G: Optional[str] = None
    H: Optional[str] = None
    C: Optional[str] = None
    which: str = "ogata"
    method: str = "acker"
    poles: Optional[str] = None
    observer_mode: str = "current"
    K1: Optional[str] = None
    K2: Optional[str] = None
    N: int = 10
    ref: str = "step"
    use_observer: bool = False
    Ke: Optional[str] = None
    T: Optional[str] = None
    csv: Optional[str] = None
    out: Optional[str] = None
    plot: bool = False
    savefig: Optional[str] = None
    plotly: bool = False
    html: Optional[str] = None
    open_html: bool = False
    eq: bool = False
    eq_stdout: bool = False
    eq_file: Optional[str] = None

@dataclass
class DesignResult:
    K1: List[List[float]]
    K2: List[List[float]]
    meta: Dict[str, Any]

@dataclass
class ObserverResult:
    Ke: List[List[float]]
    T: List[List[float]]
    notes: str

@dataclass
class SimResult:
    y: List[float]
    u: List[float]
    k0_u: float
    summary: Dict[str, Any]
