
import sympy as sp
from state_space.stateSolverTool.io import parse_matrix, parse_vector, parse_scalar_expr, fmt_matrix_for_console, latex_mat

def test_parse_matrix_and_vector_basic():
    M = parse_matrix("[[1,2],[3,4]]")
    assert M.shape == (2,2)
    v = parse_vector("[1,2]")
    assert v.shape == (2,1)
    assert fmt_matrix_for_console(M).startswith("[[1, 2]; [3, 4]]")

def test_parse_scalar_with_k_and_latex():
    e = parse_scalar_expr("0.9**k", allow_k=True)
    k = sp.symbols('k', integer=True)
    assert e.has(k)
    # latex_mat just shouldn't crash
    A = parse_matrix("[[1,0],[0,1]]")
    _ = latex_mat(A)
