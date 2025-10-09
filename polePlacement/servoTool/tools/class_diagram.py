from __future__ import annotations
import os
from textwrap import dedent

PUML = dedent(r"""
@startuml servoTool_class_diagram
skinparam classAttributeIconSize 0
title polePlacement.servoTool - Class Diagram

package polePlacement.servoTool {
  class ServoApp
  class RunRequest
  class DesignResult
  class ObserverResult
  class SimResult

  class MinObserver {
    +Ke : ndarray
    +T  : ndarray
  }

  ServoApp --> RunRequest
  ServoApp --> DesignResult
  ServoApp --> ObserverResult
  ServoApp --> SimResult
  ServoApp --> MinObserver
}

@enduml
""")

def main(out_dir: str = "out"):
    here = os.path.dirname(__file__)
    out = os.path.abspath(os.path.join(here, "..", out_dir, "servoTool_class_diagram.puml"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(PUML)
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()
