#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate a PlantUML class diagram (.puml) for kalmanFilterTool.

Usage
-----
Inside kalmanFilters/kalmanFilterTool/:
    python tools/class_diagram.py --out out

From project root:
    python -m kalmanFilters.kalmanFilterTool.tools.class_diagram --out kalmanFilters/kalmanFilterTool/out
"""
from __future__ import annotations

import os
import argparse
from textwrap import dedent

PUML = dedent(r"""
@startuml kalmanFilterTool_class_diagram
skinparam classAttributeIconSize 0
title kalmanFilters.kalmanFilterTool — Class Diagram

package kalmanFilters.kalmanFilterTool {
  class KalmanModel { }
  class Simulator { }
  class SimulationResult { }
  class KalmanFilterApp { }
  class CSVExporter { }
  class Plotter { }
}

KalmanFilterApp --> Simulator
Simulator --> KalmanModel
Simulator --> SimulationResult
KalmanFilterApp --> CSVExporter
KalmanFilterApp --> Plotter
@enduml
""")

# Detect if running as a script inside the package (no __package__)
_INSIDE_PACKAGE = (__package__ in (None, ""))

def _default_out_dir() -> str:
    return "out" if _INSIDE_PACKAGE else "kalmanFilters/kalmanFilterTool/out"

def main() -> str:
    ap = argparse.ArgumentParser(description="Emit PlantUML .puml diagram for kalmanFilterTool")
    ap.add_argument("--out", dest="out_dir", default=_default_out_dir(), help="Output directory")
    ap.add_argument("--filename", default="kalmanFilterTool_class_diagram.puml", help="Output filename")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    path = os.path.join(args.out_dir, args.filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(PUML)
    print(f"Wrote {path}")
    return path

if __name__ == "__main__":
    main()
