
from __future__ import annotations
from typing import Dict, Any
import sympy as sp

def _nsimplify_matrix_entries(M, symbols_map):
    def _ns(x):
        try:
            return sp.nsimplify(x, rational=True, maxsteps=50)
        except Exception:
            return sp.sympify(x, locals=symbols_map)
    return M.applyfunc(_ns)

def parse_matrix(s: str, allow_k: bool = False) -> sp.Matrix:
    k = sp.symbols('k', integer=True)
    symbols_map = {'k': k} if allow_k else {}
    try:
        obj = sp.sympify(s, locals=symbols_map)
    except Exception:
        obj = eval(s, {"__builtins__": {}}, symbols_map)

    if isinstance(obj, sp.MatrixBase):
        M = sp.Matrix(obj)
    elif isinstance(obj, (list, tuple)):
        if len(obj) == 0:
            raise ValueError("Empty list is not a valid matrix.")
        if all(isinstance(r, (list, tuple, sp.MatrixBase)) for r in obj):
            M = sp.Matrix(obj)
        else:
            M = sp.Matrix([list(obj)])
    else:
        raise ValueError("Matrix must be a list, list of lists, or a SymPy Matrix.")
    return _nsimplify_matrix_entries(M, symbols_map)

def parse_vector(s: str, allow_k: bool = False) -> sp.Matrix:
    M = parse_matrix(s, allow_k=allow_k)
    if M.rows == 1 and M.cols > 1:
        M = M.T
    if M.cols != 1:
        raise ValueError("Vector must be a single column (e.g. [1,2,3] or [[1],[2],[3]]).")
    return M

def parse_scalar_expr(s: str, allow_k: bool = False) -> sp.Expr:
    k = sp.symbols('k', integer=True)
    symbols_map = {'k': k} if allow_k else {}
    e = sp.sympify(s, locals=symbols_map)
    try:
        e = sp.nsimplify(e, rational=True, maxsteps=50)
    except Exception:
        pass
    return e

def fmt_matrix_for_console(M: sp.Matrix) -> str:
    def s(x): return sp.sstr(x)
    rows = ["[" + ", ".join(s(M[i, j]) for j in range(M.cols)) + "]" for i in range(M.rows)]
    return "[{}]".format("; ".join(rows))

def latex_mat(M: sp.Matrix) -> str:
    return sp.latex(M)
