from __future__ import annotations
from textwrap import dedent
import os
PUML = dedent('''
@startuml polynomialTool_class_diagram
skinparam classAttributeIconSize 0
title polynomialEquations.polynomialTool — Class Diagram
package polynomialEquations.polynomialTool {
  class PolynomialApp { + run(req: RunRequest) Dict }
  class RunRequest { + mode; +A; +B; +layout; +d; +degS; +degR; +pretty; +show_E; +export_json; +export_csv; +backend; +save; +T; +kmax; +D/H/F/config/ogata_parity; +Gmodel_num/Gmodel_den/H1; +rst_config }
  class core { +diophantine(...); +ogata_sylvester_E(...); +sylvester_matrix_desc(...); +poly_conv_desc(...); +poly_at1_desc(...) }
  class design { +solve_alpha_beta(...); +polydesign(...); +rst_design(...); +model_match(...) }
  class io { +parse_coeffs(...); +save_json(...); +save_csv(...) }
}
PolynomialApp --> RunRequest
PolynomialApp --> design
design --> core
PolynomialApp --> io
@enduml
''')
def main():
    out = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'out', 'polynomialTool_class_diagram.puml'))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out,'w') as f: f.write(PUML)
    print('Wrote', out)
if __name__=='__main__': main()
