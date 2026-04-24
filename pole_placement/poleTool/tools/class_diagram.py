from __future__ import annotations
from textwrap import dedent
from pathlib import Path

PUML = dedent(r"""
@startuml pole_placement.poleTool_class_diagram
skinparam classAttributeIconSize 0
title pole_placement.poleTool — Class Diagram

package pole_placement.poleTool {
  class PolePlacementApp {
    + run(req: RunRequest) : Dict[str, Any]
  }

  class RunRequest {
    + A: str
    + B: str
    + C: str
    + json_in: str
    + poles: str
    + deadbeat: bool
    + method: str
    + samples: int
    + plot: str
    + style: str
    + pretty: bool
    + save_json: bool
    + save_csv: bool
    + name: str
    + outdir: str
  }
}

RunRequest <.. PolePlacementApp : uses

@enduml
""")

def main(out: str = "out"):
    outdir = Path(__file__).resolve().parents[1] / out
    outdir.mkdir(parents=True, exist_ok=True)
    p = outdir / "poleTool_class_diagram.puml"
    p.write_text(PUML, encoding="utf-8")
    print(f"Wrote {p}")

if __name__ == "__main__":
    main()
