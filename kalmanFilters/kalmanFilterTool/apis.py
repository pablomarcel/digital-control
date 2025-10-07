from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Literal
import numpy as np

Backend = Literal["mpl", "plotly", "both", "none"]

@dataclass
class RunRequest:
    dt: float = 0.05
    T: float = 10.0
    q: float = 0.25
    r: float = 4.0
    u: float = 0.0
    steady: bool = False
    seed: int = 1
    backend: Backend = "both"
    A: Optional[np.ndarray] = None
    B: Optional[np.ndarray] = None
    C: Optional[np.ndarray] = None
    G: Optional[np.ndarray] = None
    Q: Optional[np.ndarray] = None
    R: Optional[np.ndarray] = None
    x0: Optional[np.ndarray] = None
    P0: Optional[np.ndarray] = None
    xtrue0: Optional[np.ndarray] = None
    save_csv: Optional[str] = None
    save_png: Optional[str] = None
    save_html: Optional[str] = None
    no_show: bool = False
    in_dir: str = "kalmanFilters/kalmanFilterTool/in"
    out_dir: str = "kalmanFilters/kalmanFilterTool/out"
