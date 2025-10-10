from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple
import sympy as sp

from .apis import RunRequest, RunResult
from .core import StateConverterCore
from .design import fmt, build_latex
from .io import ensure_out_dir

@dataclass
class StateConverterApp:
    def run(self, req: RunRequest) -> RunResult:
        # Resolve examples if requested
        if req.example:
            A,B,C,D,T = self._example(req)
        else:
            assert req.A is not None and req.B is not None and req.C is not None and req.D is not None and req.T is not None
            A,B,C,D,T = req.A, req.B, req.C, req.D, req.T

        # Fast numeric path if evalf was requested and all numeric
        if req.evalf is not None and all(len(X.free_symbols)==0 for X in (A,B,C,D,T if isinstance(T, sp.Expr) else sp.sympify(T))):
            A = sp.N(A, req.evalf); B = sp.N(B, req.evalf)
            C = sp.N(C, req.evalf); D = sp.N(D, req.evalf)
            T = sp.N(T, req.evalf)

        core = StateConverterCore(simplify=req.simplify, allow_singular_fallback=req.allow_singular_fallback)

        G = core.compute_G(A, T)
        try:
            H = core.compute_H(A, G, B, T)
        except Exception as e:
            # SymPy raises either NonInvertibleMatrixError or a ValueError with rank-check text.
            noninv = getattr(sp.matrices, "exceptions", None)
            is_noninv = False
            if noninv is not None:
                NIE = getattr(noninv, "NonInvertibleMatrixError", None)
                if NIE is not None and isinstance(e, NIE):
                    is_noninv = True
            rank_msg = "Rank of matrix is strictly less than" in str(e)
            if (is_noninv or rank_msg) and not req.allow_singular_fallback:
                raise RuntimeError(
                    "Singular A detected and --no-fallback was used. "
                    "H(T) via A^{-1}(G-I)B is undefined. "
                    "Remove --no-fallback to use the augmented expm fallback."
                ) from e
            # Otherwise re-raise original
            raise

        Finv, F = core.compute_F(G, H, C, D, req.force_inverse)

        latex_text = None
        if req.want_latex or req.latex_out:
            latex_text = build_latex(A,B,C,D,T,G,H,Finv,F)
            if req.latex_out:
                ensure_out_dir(req.latex_out)
                with open(req.latex_out, "w", encoding="utf-8") as f:
                    f.write(latex_text)

        return RunResult(G=G, H=H, F=F, Finv=Finv, latex=latex_text)

    # --- examples ---
    def _example(self, req: RunRequest):
        name = req.example
        if name == "ogata_5_4":
            a = sp.symbols('a', positive=True, real=True)
            A = sp.Matrix([[-a]])
            B = sp.Matrix([[1]])
            C = sp.Matrix([[1]])
            D = sp.Matrix([[0]])
            T = sp.sympify(req.T if req.T is not None else 'T', rational=True)
            return A,B,C,D,T
        if name == "ogata_5_5":
            A = sp.Matrix([[0, 1],
                           [0,-2]])
            B = sp.Matrix([[0],[1]])
            C = sp.Matrix([[1, 0]])
            D = sp.Matrix([[0]])
            T = sp.sympify(req.T if req.T is not None else 1, rational=True)
            return A,B,C,D,T
        if name == "matlab_p318":
            A = sp.Matrix([[0, 1],
                           [-25, -4]])
            B = sp.Matrix([[0],[1]])
            C = sp.Matrix([[1, 0]])
            D = sp.Matrix([[0]])
            T_default = sp.Rational(5, 100)  # 0.05 s
            T = sp.sympify(req.T if req.T is not None else T_default, rational=True)
            return A,B,C,D,T
        raise ValueError(f"Unknown example: {name}")
