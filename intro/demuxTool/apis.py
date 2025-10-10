from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable, List, Dict, Any, Optional

@dataclass(frozen=True)
class RunRequest:
    """Immutable request for a demux simulation run."""
    n_outputs: int = 4
    data_bw: int = 8
    strict: bool = False
    # input sources: one of csv_path or json_spec (inline or path)
    csv_path: Optional[str] = None
    json_spec: Optional[str] = None
    # outputs
    out_csv: Optional[str] = None
    out_vcd: Optional[str] = None
    # dir policy
    in_dir: str = "in"
    out_dir: str = "out"

@dataclass
class RunResult:
    rows: List[Dict[str, int]] = field(default_factory=list)
    sel_bits: int = 1
    data_bw: int = 8
    n_outputs: int = 4
    out_csv: Optional[str] = None
    out_vcd: Optional[str] = None
