
from __future__ import annotations
import os
from textwrap import dedent

PUML = dedent(r"""
@startuml observabilityTool_class_diagram
skinparam classAttributeIconSize 0
title polePlacement.observabilityTool — Class Diagram

package polePlacement.observabilityTool {
  class ObservabilityApp {
    + run(req: RunRequest) : RunResult
  }

  class RunRequest {
    + json_in: str?
    + A: str?
    + C: str?
    + discrete: bool
    + horizon: int?
    + tol: float?
    + do_pbh: bool
    + do_gram: bool
    + finite_dt: int?
    + finite_ct: float?
    + do_minreal: bool
    + symbolic: bool
    + pretty: bool
    + name: str
    + save_csv: bool
    + save_gram: bool
    + save_json: bool
    + report: str?
  }

  class RunResult {
    + exit_code: int
    + summary_json: str?
    + files_written: List[str]
    + stdout: str?
  }
}

RunRequest --> ObservabilityApp : input
ObservabilityApp --> RunResult : output

@enduml
""")

def main(out_dir="out"):
    path = os.path.join(os.path.dirname(__file__), "..", out_dir, "observabilityTool_class_diagram.puml")
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(PUML)
    print(f"Wrote {path}")

if __name__ == "__main__":
    main()
