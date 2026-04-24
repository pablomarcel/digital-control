from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class RunRequest:
    mode: str                       # fh-dt | ct-siso-ogata | ss-lqr | servo-lqr | lyap | lyap-sweep
    infile: Optional[str] = None    # YAML path for solve mode
    name: str = "case"
    outdir: str = "out"
    plot: str = "none"              # mpl | plotly | none
    params: Optional[Dict[str, float]] = None
    sweep: Optional[str] = None     # "a=start:stop:points" for lyap-sweep override
