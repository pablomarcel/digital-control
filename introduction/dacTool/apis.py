from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class RunRequest:
    """User-facing API for a single DAC simulation run.

    You pick the `dac_type` ('r2r' or 'weighted') and pass common knobs plus paths.
    All relative paths are resolved against `in_dir`/`out_dir` by the CLI/app.
    """
    dac_type: str  # 'r2r' | 'weighted'
    nbits: int = 10
    vref: float = 3.3

    # R-2R specific
    R_ohm: float = 10_000.0
    sigma_r_pct: float = 0.0
    sigma_2r_pct: float = 0.0

    # Weighted specific
    ro_over_r: float = 1.0
    res_sigma_pct: float = 0.0

    # Common post-path non-idealities
    gain_err: float = 0.0
    vo_offset: float = 0.0

    # Vector source (exactly one required)
    csv: Optional[str] = None
    jspec: Optional[str] = None  # JSON (inline or file path)

    # Output / timing
    tupd: float = 1e-6
    in_dir: str = "in"
    out_dir: str = "out"
    out_csv: Optional[str] = None
    out_vcd: Optional[str] = None
    out_vcd_all: Optional[str] = None
    include_ideal_in_vcd: bool = False

    radix: str = "dec"  # printing/log only

@dataclass
class Update:
    code: int
    vo_ideal: float
    vo_nonideal: float

@dataclass
class Row:
    # Persisted to CSV (use design.write_results_csv)
    meta: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RunResult:
    """What the App returns; design helpers can persist this to files."""
    rows: List[Row]
    updates: List[Update]
    messages: List[str] = field(default_factory=list)
