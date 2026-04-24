#!/usr/bin/env python3
from __future__ import annotations
import os
from textwrap import dedent

PUML = dedent(r"""
@startuml controllabilityTool_class_diagram
skinparam classAttributeIconSize 0
title pole_placement.controllabilityTool — Class Diagram

package pole_placement.controllabilityTool {
  class ControllabilityApp {
    +run(req: RunRequest) : RunResult
    -_load(req: RunRequest) : Tuple[np.ndarray,...]
  }
  class RunRequest
  class RunResult
}

ControllabilityApp --> RunRequest
ControllabilityApp --> RunResult

@enduml
""")

def main():
    out = os.path.join(os.path.dirname(__file__), "..", "out", "controllabilityTool_class_diagram.puml")
    with open(out, "w") as f:
        f.write(PUML)
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()
