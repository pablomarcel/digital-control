
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class RunRequest:
    # Plant / example
    example37: bool = False
    plant_num: Optional[List[float]] = None
    plant_den: Optional[List[float]] = None
    T: Optional[float] = None

    # Controller (digital PID, analog mapping, or direct digital)
    Kp: Optional[float] = None
    Ki: Optional[float] = None
    Kd: Optional[float] = None
    K: Optional[float] = None
    Ti: Optional[float] = None
    Td: Optional[float] = None
    ctrl_numz: Optional[List[float]] = None
    ctrl_denz: Optional[List[float]] = None

    # Input
    input: str = "step"
    amp: float = 1.0
    N: int = 60

    # Pole placement
    cl_poles: Optional[List[complex]] = None

    # Two-DOF
    two_dof: bool = False
    t_design: str = "dc"
    t_beta: float = 0.85
    t_numz: Optional[List[float]] = None
    t_denz: Optional[List[float]] = None

    # Optional prefilter (1-DOF only)
    pre_numz: Optional[List[float]] = None
    pre_denz: Optional[List[float]] = None

    # Outputs
    matplotlib: Optional[str] = None
    csv: Optional[str] = None
    pzmap: Optional[str] = None
    rlocus: Optional[str] = None
    plotly_step: Optional[str] = None
    plotly_pz: Optional[str] = None
    plotly_rl: Optional[str] = None
    kmin: float = 0.0
    kmax: float = 20.0
    rlocus_log: bool = False
    rclip: float = 2.5
    pzclip: float = 2.0
    panel: Optional[str] = None

    outdir: str = "out"
    print_tf: bool = False
