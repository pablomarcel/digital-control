# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from textwrap import dedent

PUML = dedent(r"""
@startuml frequencyResponseTool_class_diagram
skinparam classAttributeIconSize 0
title systemDesign.frequencyResponseTool — Class Diagram

package systemDesign.frequencyResponseTool {
  class FrequencyResponseApp {
    +run(req: RunRequest): RunResult
  }

  class RunRequest {
  }
  class RunResult {
  }
  class LeadParams { K, alpha, tau }
  class LagParams { K, beta, tau }
  class LagLeadParams { K, beta, tau_lag, alpha, tau_lead }

  class Lead { +to_w() }
  class Lag { +to_w() }
  class LagLead { +to_w() }

  class MatplotlibPlotter { +bode(...) }
  class PlotlyPlotter { +bode(...) }
}

FrequencyResponseApp --> RunRequest
FrequencyResponseApp --> RunResult
FrequencyResponseApp --> LeadParams
FrequencyResponseApp --> LagParams
FrequencyResponseApp --> LagLeadParams
FrequencyResponseApp --> MatplotlibPlotter
FrequencyResponseApp --> PlotlyPlotter
@enduml
""")

def main(out_dir: str = "out") -> str:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "frequencyResponseTool_class_diagram.puml")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(PUML)
    print(f"Wrote {path}")
    return path

if __name__ == "__main__":
    main()
