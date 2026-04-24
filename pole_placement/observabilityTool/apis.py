
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class RunRequest:
    # Source
    json_in: Optional[str] = None
    A: Optional[str] = None
    C: Optional[str] = None
    discrete: bool = False
    horizon: Optional[int] = None
    tol: Optional[float] = None

    # Options
    do_pbh: bool = False
    do_gram: bool = False
    finite_dt: Optional[int] = None
    finite_ct: Optional[float] = None
    do_minreal: bool = False
    symbolic: bool = False

    # Output / UX
    pretty: bool = False
    name: str = "obsv"
    save_csv: bool = False
    save_gram: bool = False
    save_json: bool = False
    report: Optional[str] = None


@dataclass
class RunResult:
    exit_code: int
    summary_json: Optional[str] = None
    files_written: List[str] = field(default_factory=list)
    stdout: Optional[str] = None  # pretty-printed output (captured by app if desired)
