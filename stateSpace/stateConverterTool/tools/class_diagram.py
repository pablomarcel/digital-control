from __future__ import annotations
import os
from textwrap import dedent

PUML = dedent(r"""
@startuml stateConverterTool_class_diagram
skinparam classAttributeIconSize 0
title stateSpace.stateConverterTool — Class Diagram

package stateSpace.stateConverterTool {
  class StateConverterApp {
    +run(req: RunRequest) : RunResult
    -_example(req: RunRequest) : Tuple[Matrix, Matrix, Matrix, Matrix, Expr]
  }

  class StateConverterCore {
    +expm_AT(A, T) : Matrix
    +H_via_linear_solve(A, G, B) : Matrix
    +H_via_augmented_expm(A, B, T) : Matrix
    +pulse_transfer(G, H, C, D, force_inverse) : (Matrix?, Matrix)
    +compute_G(A, T) : Matrix
    +compute_H(A, G, B, T) : Matrix
    +compute_F(G, H, C, D, force_inverse) : (Matrix?, Matrix)
  }

  class RunRequest {
    +A: Matrix?
    +B: Matrix?
    +C: Matrix?
    +D: Matrix?
    +T: Expr?
    +example: str?
    +digits: int
    +evalf: int?
    +simplify: bool
    +force_inverse: bool
    +allow_singular_fallback: bool
    +want_latex: bool
    +latex_out: str?
  }

  class RunResult {
    +G: Matrix
    +H: Matrix
    +F: Matrix
    +Finv: Matrix?
    +latex: str?
  }

  RunRequest --> StateConverterApp : input
  StateConverterApp --> RunResult : output
  StateConverterApp --> StateConverterCore : uses
}

@enduml
""")

def main():
    out = "stateConverterTool_class_diagram.puml"
    with open(out, "w", encoding="utf-8") as f:
        f.write(PUML)
    print(f"Wrote ./{out}")

if __name__ == "__main__":
    main()
