from __future__ import annotations
from typing import List
import sympy as sp

def sone(expr) -> str:
    return sp.sstr(expr)

def fmt_matrix(M: sp.MatrixBase) -> str:
    rows = []
    for i in range(M.rows):
        row = ", ".join(sone(M[i, j]) for j in range(M.cols))
        rows.append(f"[{row}]")
    return "[" + "; ".join(rows) + "]"

def fmt(obj) -> str:
    if isinstance(obj, sp.MatrixBase):
        if obj.rows == 1 and obj.cols == 1:
            return sone(obj[0, 0])
        return fmt_matrix(obj)
    return sone(obj)

def latex_block(lines: List[str]) -> str:
    return "\n".join(lines)

def make_ct_latex(A: sp.Matrix, Q: sp.Matrix, P: sp.Matrix, hermitian: bool) -> str:
    Aop = r"A^\ast" if hermitian else r"A^\top"
    lines = []
    lines.append(r"\paragraph*{Continuous-time Lyapunov}")
    lines.append(rf"\[ A = {sp.latex(A)} \;;\; Q = {sp.latex(Q)} \]")
    lines.append(rf"\[ \text{{solve }} \; {Aop} P + P A = -Q \text{{ for }} P \]")
    lines.append(rf"\[ P = {sp.latex(P)} \]")
    lines.append(rf"\[ V(x) = x^\top P x \;,\;\; \dot V(x) = -\,x^\top Q x \]")
    return latex_block(lines)

def make_dt_latex(G: sp.Matrix, Q: sp.Matrix, P: sp.Matrix, hermitian: bool) -> str:
    Gop = r"G^\ast" if hermitian else r"G^\top"
    lines = []
    lines.append(r"\paragraph*{Discrete-time Lyapunov}")
    lines.append(rf"\[ G = {sp.latex(G)} \;;\; Q = {sp.latex(Q)} \]")
    lines.append(rf"\[ \text{{solve }} \; {Gop} P G - P = -Q \text{{ for }} P \]")
    lines.append(rf"\[ P = {sp.latex(P)} \]")
    lines.append(rf"\[ V(x) = x^\top P x \;,\;\; \Delta V(x) = -\,x^\top Q x \]")
    return latex_block(lines)
