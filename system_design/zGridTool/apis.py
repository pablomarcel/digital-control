# -*- coding: utf-8 -*-
"""
Public API surface for system_design.zGridTool
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class RunRequest:
    # Timing
    T: Optional[float] = None
    fs: Optional[float] = None

    # Grids
    zetas: List[float] = field(default_factory=lambda: [0.1,0.2,0.3,0.4,0.6,0.8])
    wd_over_ws: List[float] = field(default_factory=lambda: [0,0.1,0.2,0.25,0.3,0.4,0.5])
    wnT: List[float] = field(default_factory=lambda: [0.5,1.0,1.5,2.0])
    theta_max: float = 3.141592653589793
    settling_sigma: Optional[float] = None

    # Overlays
    pz_files: List[str] = field(default_factory=list)

    # Rendering
    backend: str = "mpl"        # "mpl" or "plotly"
    png: str = "zgrid.png"
    plotly_html: Optional[str] = None
    width: int = 900
    height: int = 900
    dpi: int = 150
    dark: bool = False
    theme: str = "plotly_white"
    legend_mode: str = "minimal"
    legend_loc: str = "bottom"
    title: str = "z-plane design grid"
    title_mode: str = "auto"
    responsive: bool = True

    # Data export
    export_csv_prefix: Optional[str] = None

    # Verbose
    verbose: bool = False

@dataclass
class RunResult:
    png_path: Optional[str] = None
    html_path: Optional[str] = None
    csv_prefix: Optional[str] = None
