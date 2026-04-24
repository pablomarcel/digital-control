
from __future__ import annotations
from typing import List, Optional
import sympy as sp
from .io import latex_mat

def lti_latex_block(G, H, C, D, x0, u_expr, inv, z, Psi, xk, yk, real_modal=None, include_zt: bool=False) -> List[str]:
    lines = []
    lines.append(r"\paragraph*{LTI system}")
    lines.append(r"\[ x_{k+1} = G\,x_k + H\,u_k,\quad y_k = C\,x_k + D\,u_k \]")
    lines.append(r"\[ G = " + latex_mat(G) + r",\quad H = " + latex_mat(H)
                 + r",\quad C = " + latex_mat(C) + r",\quad D = " + latex_mat(D) + r"\]")
    lines.append(r"\[ x(0) = " + latex_mat(x0) + r",\quad u(k) = " + sp.latex(u_expr) + r"\]")
    lines.append(r"\paragraph*{$zI-G$ and inverse}")
    lines.append(r"\[ zI - G = " + latex_mat(z*sp.eye(G.rows) - G)
                 + r",\quad (zI-G)^{-1} = " + latex_mat(inv) + r"\]")
    if include_zt:
        from .core import z_transform_block
        lines.extend(z_transform_block(G, H, C, D, x0, u_expr, z))
    lines.append(r"\paragraph*{State transition and solution}")
    lines.append(r"\[ \Psi(k) = G^k = " + latex_mat(Psi) + r"\]")
    if real_modal is not None:
        lines.append(r"\[ \tilde{\Psi}(k) = " + latex_mat(real_modal) + r"\]")
    ykM = (sp.Matrix([[yk]]) if not isinstance(yk, sp.MatrixBase) else yk)
    lines.append(r"\[ x(k) = " + latex_mat(xk) + r",\qquad y(k) = " + latex_mat(ykM) + r"\]")
    return lines
