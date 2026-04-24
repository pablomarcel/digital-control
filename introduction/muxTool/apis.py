
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Iterable, Dict, Any, List

@dataclass(frozen=True)
class RunRequest:
    """Immutable run request for MuxApp."""
    csv: Optional[str] = None
    json: Optional[str] = None
    out: Optional[str] = None
    bits: int = 8
    trace: Optional[str] = None
    in_dir: str = "in"
    out_dir: str = "out"

@dataclass
class RunResult:
    """Results returned by a run: rows (list of dict), and any file outputs."""
    rows: List[Dict[str, Any]]
    out_csv: Optional[str] = None
    out_vcd: Optional[str] = None
