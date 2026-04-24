
from __future__ import annotations
import os
from textwrap import dedent

PUML = dedent('''
@startuml discreteResponseTool_class_diagram
skinparam classAttributeIconSize 0
title z_plane_analysis.discreteResponseTool - Class Diagram

package z_plane_analysis.discreteResponseTool {
  class DiscreteResponseApp {
    +__init__(req: RunRequest)
    +run(...) : Dict
  }

  class RunRequest {
    +example37: bool
    +plant_num: List[float]
    +plant_den: List[float]
    +T: float
    ..controller..
    +Kp,Ki,Kd: float
    +K,Ti,Td: float
    +ctrl_numz, ctrl_denz: List[float]
    ..input..
    +input: str
    +amp: float
    +N: int
    ..placement..
    +cl_poles: List[complex]
    ..2dof..
    +two_dof: bool
    +t_design: str
    +t_beta: float
    +t_numz, t_denz: List[float]
    ..prefilter..
    +pre_numz, pre_denz: List[float]
    ..outputs..
    +matplotlib, csv, pzmap, rlocus: str
    +plotly_step, plotly_pz, plotly_rl: str
    +kmin, kmax, rlocus_log, rclip, pzclip: float/bool
    +panel: str
    +outdir: str
    +print_tf: bool
  }
}
@enduml
''')

def main(out_dir: str = "out"):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "discreteResponseTool_class_diagram.puml")
    with open(path, "w") as f:
        f.write(PUML)
    print("Wrote", path)

if __name__ == "__main__":
    main()
