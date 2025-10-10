from __future__ import annotations
import os
from textwrap import dedent

PUML = dedent(r"""
@startuml adcTool_class_diagram
skinparam classAttributeIconSize 0
title intro.adcTool — Class Diagram

package "intro.adcTool" {
  class ADCApp {
    +run(req: RunRequest): RunResult
  }

  class RunRequest
  class RunResult
  class SampleSummary

  abstract class ADCBase {
    +simulate_sample(vin: float): (summary, trace)
    -_gauss_dt(mean: float): float
    #nbits: int
    #vref: float
    #comp_offset: float
    #dac_gain: float
    #dac_offset: float
    #jitter_rms: float
  }

  class CounterADC {
    +tclk: float
  }
  class SARADC {
    +tbit: float
  }

  ADCBase <|-- CounterADC
  ADCBase <|-- SARADC
  ADCApp --> RunRequest
  ADCApp --> RunResult
  ADCApp ..> ADCBase : uses
  ADCApp ..> write_vcd_counter
  ADCApp ..> write_vcd_sar
}

@enduml
""")

def main(out: str = "out"):
  os.makedirs(out, exist_ok=True)
  path = os.path.join(out, "adcTool_class_diagram.puml")
  with open(path, "w") as f:
    f.write(PUML)
  print(f"Wrote {path}")

if __name__ == "__main__":
  main()
