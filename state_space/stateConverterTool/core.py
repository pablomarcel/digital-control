from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple
import sympy as sp
from .utils import step

def _is_numeric(x) -> bool:
    if isinstance(x, sp.MatrixBase):
        return len(x.free_symbols) == 0
    return len(sp.sympify(x).free_symbols) == 0

@dataclass
class StateConverterCore:
    simplify: bool = True
    allow_singular_fallback: bool = True

    # --- math primitives ---
    @step("expm(A T)")
    def expm_AT(self, A: sp.Matrix, T) -> sp.Matrix:
        return sp.exp(A * T)

    @step("H via linear solve")
    def H_via_linear_solve(self, A: sp.Matrix, G: sp.Matrix, B: sp.Matrix) -> sp.Matrix:
        rhs = (G - sp.eye(A.shape[0])) * B
        return A.LUsolve(rhs)

    @step("H via augmented expm")
    def H_via_augmented_expm(self, A: sp.Matrix, B: sp.Matrix, T) -> sp.Matrix:
        n, r = A.shape[0], B.shape[1]
        Zrn = sp.zeros(r, n)
        Zrr = sp.zeros(r, r)
        M = sp.BlockMatrix([[A, B], [Zrn, Zrr]]).as_explicit()
        EM = sp.exp(M * T)
        return EM[:n, n:n+r]

    @step("Pulse TF")
    def pulse_transfer(self, G: sp.Matrix, H: sp.Matrix, C: sp.Matrix, D: sp.Matrix,
                       force_inverse: bool) -> Tuple[Optional[sp.Matrix], sp.Matrix]:
        z = sp.symbols('z')
        n = G.shape[0]
        Zinvg = z * sp.eye(n) - G
        Finv = None
        if force_inverse:
            Finv = Zinvg.inv()
            X = Finv * H
        else:
            X = Zinvg.LUsolve(H)
        Fz = C * X + D
        if self.simplify:
            Fz = Fz.applyfunc(lambda e: sp.cancel(sp.together(e)))
            if Finv is not None:
                Finv = Finv.applyfunc(lambda e: sp.cancel(sp.together(e)))
        return Finv, Fz

    # --- high level ---
    def compute_G(self, A: sp.Matrix, T) -> sp.Matrix:
        G = self.expm_AT(A, T)
        return sp.simplify(G) if self.simplify else G

    def compute_H(self, A: sp.Matrix, G: sp.Matrix, B: sp.Matrix, T) -> sp.Matrix:
        try:
            H = self.H_via_linear_solve(A, G, B)
        except Exception:
            if not self.allow_singular_fallback:
                raise
            H = self.H_via_augmented_expm(A, B, T)
        return sp.simplify(H) if self.simplify else H

    def compute_F(self, G: sp.Matrix, H: sp.Matrix, C: sp.Matrix, D: sp.Matrix,
                  force_inverse: bool) -> Tuple[Optional[sp.Matrix], sp.Matrix]:
        return self.pulse_transfer(G, H, C, D, force_inverse)
