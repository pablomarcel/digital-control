from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

@dataclass
class RunRequest:
    vcd: str
    signals: List[str] | None = None
    units: str = "us"                # x-axis display units for plots
    backend: str = "mpl"             # 'mpl' or 'plotly'
    overlay: bool = False            # plotly overlay
    out_csv: Optional[str] = None
    csv_units: str = "s"             # time units used in CSV export
    png: Optional[str] = None
    html: Optional[str] = None
    decode: List[Tuple[str,int]] = field(default_factory=list)
    in_dir: str = "in"
    out_dir: str = "out"

    def validate(self) -> None:
        if self.backend not in ("mpl","plotly"):
            raise ValueError("backend must be 'mpl' or 'plotly'")
        if self.units not in ("s","ms","us","ns"):
            raise ValueError("units must be one of s, ms, us, ns")
        if self.csv_units not in ("s","ms","us","ns"):
            raise ValueError("csv_units must be one of s, ms, us, ns")
