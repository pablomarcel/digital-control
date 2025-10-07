from __future__ import annotations
import os
from textwrap import dedent

PUML = dedent(r"""
@startuml rstPlotTool_class_diagram
skinparam classAttributeIconSize 0
title rstControllers.rstPlotTool — Class Diagram

package rstControllers.rstPlotTool {
  class RSTPlotApp {
    +run(req: RunRequest): void
  }

  class RunRequest {
    +files: List[str]
    +overlay: Optional[bool]
    +backend: str
    +style: str
    +dpi: int
    +kmin: Optional[float]
    +kmax: Optional[float]
    +robust: float
    +ylimits: YLimits
    +clip: bool
    +legend: str
    +filters: OverlayFilters
    +annotate: Optional[str]
    +title: Optional[str]
  }

  class YLimits {
    +ylimY: Optional[(float,float)]
    +ylimU: Optional[(float,float)]
    +ylimE: Optional[(float,float)]
  }

  class OverlayFilters {
    +include: Optional[str]
    +exclude: Optional[str]
  }
}

RunRequest --> YLimits
RunRequest --> OverlayFilters
RSTPlotApp ..> RunRequest
@enduml
""")

def main(out_dir: str = "."):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "rstPlotTool_class_diagram.puml")
    with open(path, "w") as f:
        f.write(PUML)
    print(f"Wrote {path}")

if __name__ == "__main__":
    main("..")
