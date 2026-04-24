# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
from textwrap import dedent

PUML = dedent(r"""
@startuml zGridTool_class_diagram
skinparam classAttributeIconSize 0
title system_design.zGridTool — Class Diagram

package system_design.zGridTool {
  class ZGridApp {
    + run(req: RunRequest) : RunResult
  }

  class RunRequest {
  }

  class RunResult {
  }

  class Style {
  }

  ZGridApp --> RunRequest
  ZGridApp --> RunResult
  ZGridApp ..> Style : uses
}

@enduml
""")

def main(out_dir: str = "out"):
    p = Path(__file__).resolve().parents[1] / out_dir / "zGridTool_class_diagram.puml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(PUML)
    print(f"Wrote {p}")

if __name__ == "__main__":
    main()
