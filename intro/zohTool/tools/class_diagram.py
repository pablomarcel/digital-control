from __future__ import annotations
from textwrap import dedent
import os

PUML = dedent(r"""
@startuml zohTool_class_diagram
skinparam classAttributeIconSize 0
title intro.zohTool — Class Diagram

package intro.zohTool {
  class ZOHModel {
    +Ts: float
    +delay: float
    +droop_tau: float
    +offset: float
  }

  class ZOHSimulator {
    -model: ZOHModel
    +expand(u: List[float]) : List[IntervalEvent]
  }

  class CSVExporter {
    +write_results_csv(path: str, events: List[IntervalEvent], units: str) : void
  }

  class VCDWriter {
    +write_vcd_zoh(path: str, events: List[IntervalEvent], scale: float, idx_bits: int?) : void
  }

  class ZOHApp {
    +run(req: RunRequest) : RunResult
  }

  ZOHSimulator --> ZOHModel
  ZOHApp --> ZOHSimulator
  ZOHApp --> CSVExporter
  ZOHApp --> VCDWriter
}
@enduml
""")

def main(out_dir: str = "out") -> str:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "zohTool_class_diagram.puml")
    with open(path, "w") as f:
        f.write(PUML)
    print(f"Wrote {path}")
    return path

if __name__ == "__main__":
    main()
