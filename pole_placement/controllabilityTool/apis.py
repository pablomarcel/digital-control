from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class RunRequest:
    # Source
    json_path: Optional[str] = None
    A: Optional[str] = None
    B: Optional[str] = None
    C: Optional[str] = None
    D: Optional[str] = None
    discrete: bool = False
    horizon: Optional[int] = None
    tol: Optional[float] = None

    # State tests
    pbh: bool = False
    gram: bool = False
    finite_dt: Optional[int] = None
    finite_ct: Optional[float] = None
    minreal: bool = False
    symbolic: bool = False

    # Output controllability
    output_ctrb: bool = False
    save_output_csv: bool = False

    # Output & UI
    pretty: bool = False
    name: str = "ctrb"
    save_csv: bool = False
    save_json: bool = False
    save_gram: bool = False
    report: Optional[str] = None
    log: str = "INFO"

@dataclass
class RunResult:
    exit_code: int
    summary_json: Optional[str] = None  # JSON string
