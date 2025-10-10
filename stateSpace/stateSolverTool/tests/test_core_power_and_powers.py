
import sympy as sp
from stateSpace.stateSolverTool.core import apply_power_style, apply_power_style_to_matrix, matrix_power_symbolic

def test_apply_power_style_modes():
    k = sp.symbols('k', integer=True)
    expr = (-sp.Rational(1,5))**k
    r = apply_power_style(expr, "rational")
    i = apply_power_style(expr, "integer")
    # integer style should expand rational base
    assert isinstance(i, sp.Expr)
    M = sp.Matrix([[expr, 1],[0, expr]])
    Mr = apply_power_style_to_matrix(M, "rational")
    Mi = apply_power_style_to_matrix(M, "integer")
    assert Mr.shape == M.shape and Mi.shape == M.shape

def test_matrix_power_symbolic_diagonal():
    k = sp.symbols('k', integer=True)
    G = sp.diag(sp.Rational(1,2), sp.Rational(1,3))
    Psi, modal = matrix_power_symbolic(G, k)
    assert Psi.shape == (2,2)
    assert modal is not None
