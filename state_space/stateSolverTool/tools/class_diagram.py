#!/usr/bin/env python3
from __future__ import annotations
import os
from textwrap import dedent

PUML = dedent(r"""
@startuml stateSolverTool_class_diagram
skinparam classAttributeIconSize 0
title state_space.stateSolverTool — Class Diagram

package state_space.stateSolverTool {
  class StateSolverApp {
    +run(req: RunRequest) : RunResult
  }

  class RunRequest {
    +mode: str
    +example: str
    +G,H,C,D,x0,u: str
    +Gk,Hk,Ck,Dk: str
    +latex: bool
    +latex_out: str
    +zt: bool
    +realblocks: bool
    +steps: int
    +check: str
    +power_style: str
  }

  class RunResult
  class LTIResult
  class LTVResult
  class MatrixBundle

  StateSolverApp --> RunRequest
  RunResult *-- LTIResult
  RunResult *-- LTVResult
  LTIResult *-- MatrixBundle
}

@enduml
""").strip()

def main(out_dir="out"):
    if not os.path.isabs(out_dir):
        here = os.path.dirname(__file__)
        out_dir = os.path.join(os.path.dirname(here), "out")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "stateSolverTool_class_diagram.puml")
    with open(path, "w") as f:
        f.write(PUML + "\n")
    print(f"Wrote {path}")

if __name__ == "__main__":
    main()
