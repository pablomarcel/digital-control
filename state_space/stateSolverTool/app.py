
from __future__ import annotations
from typing import Optional, List
import sympy as sp

from .apis import RunRequest, RunResult, MatrixBundle, LTIResult, LTVResult
from .io import parse_matrix, parse_vector, parse_scalar_expr, fmt_matrix_for_console
from .core import (inverse_zI_minus_G, lti_solution, matrix_power_symbolic,
                   brief_check_lti, brief_check_ltv, example_system)
from .design import lti_latex_block
from .utils import out_path

class StateSolverApp:
    """Application orchestrator for the State Solver tool."""

    def __init__(self, pkg_dir: str):
        self.pkg_dir = pkg_dir  # directory of this package (for in/out conventions)

    # ----------------------------- run() -------------------------------------

    def run(self, req: RunRequest) -> RunResult:
        z = sp.symbols('z')
        k = sp.symbols('k', integer=True)

        if req.example:
            G, H, C, D, x0, u_expr = example_system(req.example)
            mode = "lti"
        else:
            mode = req.mode

        if mode == "lti":
            if not req.example:
                if not all([req.G, req.H, req.C, req.D, req.x0, req.u]):
                    raise ValueError("For LTI provide G,H,C,D,x0,u")
                G = parse_matrix(req.G, allow_k=False)
                H = parse_matrix(req.H, allow_k=False)
                C = parse_matrix(req.C, allow_k=False)
                D = parse_matrix(req.D, allow_k=False)
                x0 = parse_vector(req.x0, allow_k=False)
                u_expr = parse_scalar_expr(req.u, allow_k=True)

            inv, det, adj, a_list, H_list = inverse_zI_minus_G(G, z)
            Psi, xk, yk = lti_solution(G, H, C, D, x0, u_expr, k, power_style=req.power_style)

            check_status = None
            if req.check != "off":
                check_status = brief_check_lti(G, H, C, D, x0, u_expr, Psi, xk, yk, steps=req.steps)

            real_modal = None
            if req.realblocks:
                try:
                    _, real_modal = matrix_power_symbolic(G, k)
                except Exception:
                    real_modal = None

            latex_lines = None
            if req.latex:
                latex_lines = lti_latex_block(G, H, C, D, x0, u_expr, inv, z, Psi, xk, yk,
                                              real_modal=real_modal, include_zt=req.zt)
                if req.latex_out:
                    path = req.latex_out
                    if not (path.startswith("/") or path[1:3] == ":\\" or path.startswith("~")):
                        # resolve under package out/
                        path = out_path(self.pkg_dir, req.latex_out)
                    with open(path, "w") as f:
                        for L in latex_lines:
                            f.write(L + "\n")

            lti = LTIResult(
                matrices=MatrixBundle(G=G, H=H, C=C, D=D, x0=x0, u_expr=u_expr),
                zI_minus_G = z*sp.eye(G.rows) - G,
                inv_zI_minus_G = inv,
                det_zI_minus_G = det,
                adj_zI_minus_G = adj,
                leverrier_a = a_list,
                leverrier_H = H_list,
                Psi = Psi,
                xk = xk,
                yk = (sp.Matrix([[yk]]) if not isinstance(yk, sp.MatrixBase) else yk),
                check_status = check_status,
                latex_lines = latex_lines
            )
            return RunResult(mode="lti", lti=lti)

        # ----------------------------- LTV -----------------------------------
        else:
            if not all([req.Gk, req.Hk, req.Ck, req.Dk, req.x0, req.u]):
                raise ValueError("For LTV provide Gk,Hk,Ck,Dk,x0,u")
            Gk = parse_matrix(req.Gk, allow_k=True)
            Hk = parse_matrix(req.Hk, allow_k=True)
            Ck = parse_matrix(req.Ck, allow_k=True)
            Dk = parse_matrix(req.Dk, allow_k=True)
            x0 = parse_vector(req.x0, allow_k=True)
            u_expr = parse_scalar_expr(req.u, allow_k=True)

            status, Phi, xs, ys = brief_check_ltv(Gk, Hk, Ck, Dk, x0, u_expr, steps=req.steps)

            ltv = LTVResult(Phi=Phi, xs=xs, ys=ys, check_status=status, latex_lines=None)
            return RunResult(mode="ltv", ltv=ltv)
