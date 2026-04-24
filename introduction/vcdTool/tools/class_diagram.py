from __future__ import annotations
import os
from textwrap import dedent

PUML = dedent(r"""
@startuml vcdTool_class_diagram
skinparam classAttributeIconSize 0
title introduction.vcdTool — Class Diagram

package introduction.vcdTool {
  class VCDApp {
    + run(req: RunRequest) : dict
  }
  class RunRequest {
    + vcd: str
    + signals: List[str]
    + units: str
    + backend: str
    + overlay: bool
    + out_csv: str
    + csv_units: str
    + png: str
    + html: str
    + decode: List[Tuple[str,int]]
    + in_dir: str
    + out_dir: str
    + validate() : None
  }
  class VCDParser {
    + parse(path: str) : VCDData
  }
  class WaveformBuilder {
    + build(vcd: VCDData, wanted_names: List[str]) : (times, series, rawbits, widths)
  }
  class Decoder {
    + apply(series, rawbits, widths, decodes: List[Tuple[str,int]]) : None
  }
  class VCDData {
    + timescale_factor: float
    + vars_by_id: Dict[str, Var]
    + events: List[Tuple[int, List[Tuple[str,str]]]]
  }
  class design <<module>> {
    + plot_mpl(...)
    + plot_plotly(...)
  }
  class io <<module>> {
    + resolve_input_path(...)
    + resolve_output_path(...)
    + export_csv(...)
  }
}

VCDApp -> RunRequest
VCDApp -> VCDParser
VCDApp -> WaveformBuilder
VCDApp -> Decoder
VCDParser -> VCDData
@enduml
""")

def main(out_dir: str = "out") -> None:
    path = os.path.join(out_dir, "vcdTool_class_diagram.puml")
    os.makedirs(out_dir, exist_ok=True)
    with open(path, 'w') as f:
        f.write(PUML)
    print(f"Wrote {path}")

if __name__ == "__main__":
    main()
