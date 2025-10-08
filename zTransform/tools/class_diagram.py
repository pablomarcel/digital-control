#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate a PlantUML class diagram skeleton for zTransformTool.
Writes: ./out/zTransformTool_class_diagram.puml
"""
from __future__ import annotations
import os
from textwrap import dedent

PUML = dedent(r"""
@startuml zTransformTool_class_diagram
skinparam classAttributeIconSize 0
title digitalControl.zTransform.zTransformTool — Class Diagram

package zTransform.zTransformTool {
  class ZTApp {
    + run(req: RunRequest) : Dict
  }

  class RunRequest {
    + mode: str
    + expr: Optional[str]
    + xt: Optional[str]
    + X: Optional[str]
    + subs: Optional[str]
    + N: Optional[int]
    + latex: bool
    + export_csv: Optional[str]
    + export_json: Optional[str]
    + num: Optional[str]
    + den: Optional[str]
    + dt: float
    + impulse: bool
    + step: bool
    + u: Optional[str]
    + rec: Optional[str]
    + a: Optional[str]
    + rhs: Optional[str]
    + ics: Optional[str]
  }

  class core {
    + forward_z(...)
    + forward_z_from_xt(...)
    + inverse_z(...)
    + series_in_u(...)
    + scipy_residuez(...)
    + tf_util(...)
    + solve_difference(...)
  }

  class utils {
    + ensure_out_dir(...)
    + force_out_path(...)
    + pbox(...)
    + to_exportable(...)
    + symbol_table(...)
  }

  class io {
    + parse_subs(...)
    + parse_coeffs_numeric(...)
    + parse_coeffs_symbolic(...)
    + export_sequence(...)
  }

  class design {
    + box(...)
    + as_text(...)
  }

  ZTApp --> RunRequest
  ZTApp ..> core
  ZTApp ..> io
  ZTApp ..> utils
  ZTApp ..> design
}

@enduml
""").strip()

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(here, "..", "out")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "zTransformTool_class_diagram.puml")
    with open(path, "w") as f:
        f.write(PUML + "\n")
    print(f"Wrote {os.path.abspath(path)}")

if __name__ == "__main__":
    main()
