from __future__ import annotations
import os
from textwrap import dedent

PUML = dedent(r"""
@startuml dacTool_class_diagram
skinparam classAttributeIconSize 0
title intro.dacTool — Class Diagram

package intro.dacTool {
  class RunRequest {
    +dac_type: str
    +nbits: int
    +vref: float
    +R_ohm: float
    +sigma_r_pct: float
    +sigma_2r_pct: float
    +ro_over_r: float
    +res_sigma_pct: float
    +gain_err: float
    +vo_offset: float
    +csv: str
    +jspec: str
    +tupd: float
    +in_dir: str
    +out_dir: str
    +out_csv: str
    +out_vcd: str
    +out_vcd_all: str
    +include_ideal_in_vcd: bool
    +radix: str
  }

  class RunResult {
    +rows: List<Row>
    +updates: List<Update>
    +messages: List<str>
  }

  class Row { +meta: Dict }
  class Update { +code: int; +vo_ideal: float; +vo_nonideal: float }

  class WeightedDAC {
    -base: List<float>
    -nonideal: List<float>
    +vo_ideal_bits(bits): float
    +vo_nonideal_bits(bits): float
  }

  class R2RDAC {
    -_R_vals: List<float>
    -_2R_vals: List<float>
    -_w_ideal: List<float>
    -_w_non: List<float>
    +vo_ideal_bits(bits): float
    +vo_nonideal_bits(bits): float
  }

  RunRequest --> RunResult
  RunResult "1" o-- "*" Row
  RunResult "1" o-- "*" Update
  WeightedDAC ..> RunRequest : config
  R2RDAC ..> RunRequest : config
}
@enduml
""")

def main(out_dir: str = "out"):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "dacTool_class_diagram.puml")
    with open(path, "w") as f:
        f.write(PUML)
    print(f"Wrote {path}")

if __name__ == "__main__":
    main()
