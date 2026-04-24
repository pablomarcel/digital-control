
from __future__ import annotations
import os
from textwrap import dedent

PUML = dedent(r"""
@startuml observerTool_class_diagram
skinparam classAttributeIconSize 0
title pole_placement.observerTool — Class Diagram

package pole_placement.observerTool {

  class ObserverApp {
    +run(req): Dict
    -_run_example(req): Dict
  }

  class DesignRequest
  class ClosedLoopRequest
  class K0Request
  class SelectRequest
  class SimRequest
  class ExampleRequest

  ObserverApp --> DesignRequest
  ObserverApp --> ClosedLoopRequest
  ObserverApp --> K0Request
  ObserverApp --> SelectRequest
  ObserverApp --> SimRequest
  ObserverApp --> ExampleRequest
}

@enduml
""")

def main(out_dir: str = "out"):
  fname = os.path.join(os.path.dirname(__file__), "..", out_dir, "observerTool_class_diagram.puml")
  with open(fname, "w") as f:
    f.write(PUML)
  print(f"Wrote {os.path.abspath(fname)}")

if __name__ == "__main__":
  main()
