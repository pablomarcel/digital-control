
from __future__ import annotations
import os
from textwrap import dedent

PUML = dedent(r"""
@startuml transformationTool_class_diagram
skinparam classAttributeIconSize 0
title pole_placement.transformationTool — Class Diagram

package pole_placement.transformationTool {
  class TransformationApp {
    + run(req: RunRequest) : List<TransformResult>
  }

  class RunRequest {
    + A: ndarray
    + B: ndarray
    + C: ndarray
    + D: ndarray
    + to_ccf: bool
    + to_ocf: bool
    + to_diag: bool
    + to_jordan: bool
    + pretty: bool
    + name: str
    + save_json: bool
    + save_csv: bool
  }

  class TransformResult {
    + name: str
    + form: str
    + eigvals: List<complex>
    + T: ndarray
    + Ahat: ndarray
    + Bhat: ndarray
    + Chat: ndarray
    + Dhat: ndarray
  }
}

TransformationApp --> RunRequest
TransformationApp --> TransformResult
@enduml
""")

def main(outdir: str = "out"):
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "transformationTool_class_diagram.puml")
    with open(path, "w") as f:
        f.write(PUML)
    print(f"Wrote {path}")

if __name__ == "__main__":
    main()
