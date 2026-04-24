from __future__ import annotations
from textwrap import dedent
import os
PUML = dedent(r"""
@startuml quadraticTool_class_diagram
skinparam classAttributeIconSize 0
title quadratic_control.quadraticTool — Class Diagram

package quadratic_control.quadraticTool {
  class QuadraticApp
  class FiniteHorizonLQR
  class CTtoDTWeights
  class SteadyStateLQR
  class ServoLQR
  class LyapunovAnalyzer
  class LyapunovSweep
}

QuadraticApp --> FiniteHorizonLQR
QuadraticApp --> CTtoDTWeights
QuadraticApp --> SteadyStateLQR
QuadraticApp --> ServoLQR
QuadraticApp --> LyapunovAnalyzer
QuadraticApp --> LyapunovSweep

@enduml
""")

def main():
    out = os.path.join(os.path.dirname(os.path.dirname(__file__)), "out", "quadraticTool_class_diagram.puml")
    with open(out, "w") as f:
        f.write(PUML)
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()
