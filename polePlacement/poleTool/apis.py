from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class RunRequest:
    """User-facing API request for a pole-placement design & simulation run."""
    A: str | None = None              # matrix string "a b; c d"
    B: str | None = None
    C: str | None = None
    json_in: Optional[str] = None     # path to JSON with keys A,B,C
    poles: Optional[str] = None       # "0.5+0.5j,0.5-0.5j"
    deadbeat: bool = False
    method: str = "auto"              # auto|ackermann|ogata|eigs|place
    samples: int = 60
    plot: str = "mpl"                 # mpl|plotly|none
    style: str = "dots"               # dots|stairs|connected
    pretty: bool = False
    save_json: bool = False
    save_csv: bool = False
    name: str = "pole_place"
    outdir: Optional[str] = None      # override default out folder
    log: str = "INFO"                 # logging level
