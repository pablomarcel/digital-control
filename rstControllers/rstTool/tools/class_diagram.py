from __future__ import annotations
import os

PUML = """@startuml rstTool_class_diagram
skinparam classAttributeIconSize 0
title rstControllers.rstTool — Class Diagram
package rstControllers.rstTool {
  class RSTApp { +run(req: RunRequest) : RunResult }
  class RunRequest
  class RunResult
  class DiophantineSolver { +solve(A,B,d,Acl,degS,degR,integrator,alloc) : (S,R) }
  class TSelector { +choose(mode,B,Acl,Ac,Ao,T_manual,integrator,R) : T }
  class Simulator { +simulate(A,B,d,R,S,Tq,N,r_step,v_step,v_k0,noise_sigma) : SimResult }
  class SimResult
  RSTApp --> RunRequest
  RSTApp --> RunResult
  RSTApp --> DiophantineSolver
  RSTApp --> TSelector
  RSTApp --> Simulator
  Simulator --> SimResult
}
@enduml
"""

def _pkg_dir() -> str:
    # file is .../rstControllers/rstTool/tools/class_diagram.py
    # package dir is one level up from tools/
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def main(out_dir: str | None = None, fname: str = "rstTool_class_diagram.puml"):
    pkg = _pkg_dir()
    out_base = os.path.join(pkg, "out") if out_dir is None else out_dir
    os.makedirs(out_base, exist_ok=True)
    path = os.path.join(out_base, fname)
    with open(path, "w") as f:
        f.write(PUML + "\n")
    print(f"Wrote {path}")

if __name__ == "__main__":
    main()
