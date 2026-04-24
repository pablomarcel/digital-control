# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

@dataclass(frozen=True)
class LeadParams:
    K: float
    alpha: float
    tau: float

@dataclass(frozen=True)
class LagParams:
    K: float
    beta: float
    tau: float

@dataclass(frozen=True)
class LagLeadParams:
    K: float
    beta: float
    tau_lag: float
    alpha: float
    tau_lead: float

@dataclass(frozen=True)
class RunRequest:
    T: float
    gz_num_desc: List[float]
    gz_den_desc: List[float]
    mode: str                     # none | lead | lag | laglead | auto
    lead: Optional[LeadParams] = None
    lag: Optional[LagParams] = None
    laglead: Optional[LagLeadParams] = None
    # auto specs
    pm_req: float = 50.0
    gm_req: float = 10.0
    Kv_req: float = 2.0
    # plotting
    use_mpl: bool = False
    save_mpl: bool = False
    use_plotly: bool = True
    plotly_fmt: str = "html"
    # step
    step_N: int = 0
    # IO
    out_dir: str = "out"

@dataclass
class Margins:
    nu_gc: Optional[float]
    nu_pc: Optional[float]
    pm_deg: Optional[float]
    gm_db: Optional[float]

@dataclass
class RunFiles:
    path: str
    desc: str

@dataclass
class RunResult:
    Gd_w_num_asc: List[float]
    Gd_w_den_asc: List[float]
    Gd_z_num_desc: List[float]
    Gd_z_den_desc: List[float]
    L_num_desc: List[float]
    L_den_desc: List[float]
    CL_num_desc: List[float]
    CL_den_desc: List[float]
    margins: Margins
    files: List[RunFiles] = field(default_factory=list)
