
from __future__ import annotations
from textwrap import dedent
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "out"

PUML = dedent(r"""
@startuml juryTestTool_class_diagram
skinparam classAttributeIconSize 0
title system_design.juryTestTool — Class Diagram

package system_design.juryTestTool {
  class JuryTestApp { +run(req: RunRequest): RunResult }
  class StabilityDesigner {
    -tols: Tolerances
    +run_methods(...): dict
  }
  class Tolerances { +abs_tol: float; +rel_tol: float; +unit_tol: float }
  class RunRequest
  class RunResult
  class MethodResult
}

JuryTestApp ..> RunRequest
JuryTestApp ..> RunResult
JuryTestApp ..> StabilityDesigner
StabilityDesigner ..> Tolerances
RunResult ..> MethodResult

@enduml
""")

def main():
    OUT.mkdir(exist_ok=True, parents=True)
    p = OUT / "juryTestTool_class_diagram.puml"
    p.write_text(PUML)
    print(f"Wrote {p}")

if __name__ == "__main__":
    main()
