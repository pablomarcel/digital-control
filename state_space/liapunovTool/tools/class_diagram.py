from __future__ import annotations
import os
from textwrap import dedent

PUML = dedent(r"""
@startuml liapunovTool_class_diagram
skinparam classAttributeIconSize 0
title state_space.liapunovTool — Class Diagram

package state_space.liapunovTool {
  class LyapunovApp {
    +run(req: RunRequest) : RunResult
  }

  class RunRequest <<dataclass>> {
    +mode: "ct"|"dt"|"example"
    +A: str
    +G: str
    +Q: str
    +hermitian: bool
    +digits: int
    +evalf: int
    +latex: bool
    +latex_out: str
    +which: str
  }

  class RunResult <<dataclass>> {
    +mode: str
    +hermitian: bool
    +P: Matrix
    +pd_class: str
    +latex_text: str
    +meta: dict
  }

  class LyapunovSolver {
    +solve_ct(A: Matrix, Q: Matrix, hermitian: bool) : Matrix
    +solve_dt(G: Matrix, Q: Matrix, hermitian: bool) : Matrix
  }

  class PDClassifier {
    +sylvester_pd(P: Matrix, digits: int) : str
  }

  class PBuilder {
    +build(n:int, hermitian:bool) : PUnknown
  }

  class PUnknown <<dataclass>> {
    +P: Matrix
    +unknowns: list
  }
}

RunRequest --> LyapunovApp : used by
LyapunovApp --> LyapunovSolver : uses
LyapunovApp --> PDClassifier : uses
PBuilder --> PUnknown : creates
LyapunovSolver --> PBuilder : uses

@enduml
""")

def main():
    out_dir = "out"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "liapunovTool_class_diagram.puml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(PUML)
    print(f"Wrote ./{path}")

if __name__ == "__main__":
    main()
