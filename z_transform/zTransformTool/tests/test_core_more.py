# -*- coding: utf-8 -*-
import sympy as sp
import pytest
from z_transform.zTransformTool import core
from z_transform.zTransformTool.utils import symbol_table

def test_forward_from_xt_matches_forward_simple():
    syms = symbol_table()
    xk1, X1 = core.forward_z("cos(w*T*k)", syms, subs={"T":1.0,"w":0.2})
    xk2, X2 = core.forward_z_from_xt("cos(w*t)", syms, subs={"T":1.0,"w":0.2})
    assert sp.simplify(X1 - X2) == 0

def test_series_coefficients_match_manual():
    syms = symbol_table()
    ser, coeffs = core.series_in_u("z**-1/(1 - 0.5*z**-1)", syms, 5)
    # x[k] = 0.5^{k-1} for k>=1, with x[0]=0
    assert float(sp.N(coeffs[0])) == 0
    assert abs(float(sp.N(coeffs[1])) - 1.0) < 1e-9
    assert abs(float(sp.N(coeffs[2])) - 0.5) < 1e-9
    assert abs(float(sp.N(coeffs[3])) - 0.25) < 1e-9

def test_inverse_unilateral_delta_sum():
    syms = symbol_table()
    X = "1 + 2*z**-1"
    xk_closed, seq = core.inverse_z(X, syms, N=3)
    k = syms["k"]
    # Check closed form at small k
    assert sp.simplify(xk_closed.subs({k:0})) == 1
    assert sp.simplify(xk_closed.subs({k:1})) == 2
    assert seq[:2] == [1,2]

def test_difference_nonhomog_rsolve():
    syms = symbol_table()
    # x(k+1) - x(k) = 1, x(0)=0 => x(k)=k
    a = [1, -1]   # a0=1, a1=-1  -> x(k+1) - x(k)
    ics = {sp.Function('x')(0): 0}
    eq, sol, seq = core.solve_difference(a, rhs=1, ics=ics, syms=syms, N=5)
    k = syms["k"]
    for i in range(6):
        assert int(sp.N(sol.subs({k:i}))) == i
