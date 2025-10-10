from __future__ import annotations
import sympy as sp

def sone(expr) -> str:
    """Sympy single-line string."""
    return sp.sstr(expr)

def fmt_matrix(M: sp.MatrixBase) -> str:
    rows = []
    for i in range(M.rows):
        row = ", ".join(sone(M[i, j]) for j in range(M.cols))
        rows.append(f"[{row}]")
    return "[" + "; ".join(rows) + "]"

def fmt(obj) -> str:
    if isinstance(obj, sp.MatrixBase):
        if obj.shape == (1,1):
            return sone(obj[0,0])
        return fmt_matrix(obj)
    return sone(obj)

def latex_scalar_or_matrix(X) -> str:
    if isinstance(X, sp.MatrixBase) and X.shape == (1,1):
        return sp.latex(X[0,0])
    return sp.latex(X)

def build_latex(A,B,C,D,T,G,H,Finv,F) -> str:
    z = sp.symbols('z')
    Zinvg = z*sp.eye(G.shape[0]) - G
    blocks = []
    blocks.append(r"\paragraph*{Continuous-time}")
    blocks.append(
        rf"\[ A = {sp.latex(A)} ,\; B = {sp.latex(B)} ,\; C = {sp.latex(C)} ,\; "
        rf"D = {latex_scalar_or_matrix(D)} ,\; T = {sp.latex(T)}\]"
    )
    blocks.append(r"\paragraph*{ZOH discretization}")
    blocks.append(r"\[ G(T)=e^{AT},\quad H(T)=A^{-1}(G-I)B \]")
    blocks.append(rf"\[ G(T) = {sp.latex(G)} ,\quad H(T) = {sp.latex(H)} \]")
    blocks.append(r"\paragraph*{Pulse transfer function}")
    if Finv is not None:
        blocks.append(rf"\[ (zI-G)^{{-1}} = {sp.latex(Finv)} \]")
    else:
        X = Zinvg.LUsolve(H)
        blocks.append(rf"\[ (zI-G)^{{-1}}H = {sp.latex(X)} \]")
    blocks.append(rf"\[ F(z) = C\,(zI-G)^{{-1}}H + D \;=\; {sp.latex(F)} \]")
    return "\n".join(blocks)
