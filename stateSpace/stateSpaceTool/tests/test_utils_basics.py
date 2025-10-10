
import numpy as np
import sympy as sp
from stateSpace.stateSpaceTool.utils import to_float_list, coeffs_desc_to_expr, expr_to_poly, json_matrix, sympy_matrix_from_numpy, zdomain_coeffs_from_ba

def test_to_float_list_and_coeffs_to_expr_and_back():
    lst = to_float_list("1, 2; 3  4")
    assert lst == [1.0, 2.0, 3.0, 4.0]
    z = sp.symbols('z')
    expr = coeffs_desc_to_expr(lst, z)
    poly = expr_to_poly(expr, z)
    assert poly.degree() == 3
    assert [float(c) for c in poly.all_coeffs()] == [1.0,2.0,3.0,4.0]

def test_json_and_sympy_matrix_helpers():
    M = np.array([[1+0j, 2+3j],[0, -4j]], dtype=complex)
    J = json_matrix(M)
    # complex entries serialized as [re, im]
    assert J[0][1] == [2.0, 3.0]
    S = sympy_matrix_from_numpy(M)
    assert S.shape == (2,2)

def test_zdomain_coeffs_from_ba_shapes():
    b,a = [0,1,1], [1.3, 0.4]
    num, den = zdomain_coeffs_from_ba(b,a)
    assert len(num) == len(a)+1 and len(den) == len(a)+1
