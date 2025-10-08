# -*- coding: utf-8 -*-
import sympy as sp
from zTransform.zTransformTool import core
from zTransform.zTransformTool.utils import symbol_table

def test_inverse_finite_length():
    """
    Finite-length sequence: X(z) = 1 + 2 z^{-1} + 3 z^{-2} + 4 z^{-3}
    Expect x[0..3] = 1, 2, 3, 4.
    """
    syms = symbol_table()
    xk_closed, seq = core.inverse_z("1 + 2*z**-1 + 3*z**-2 + 4*z**-3", syms, N=5)
    assert seq[:4] == [1, 2, 3, 4]
    # closed form for finite-length should be combination of Kronecker deltas
    k = syms["k"]
    assert sp.simplify(xk_closed.subs({k: 0})) == 1
    assert sp.simplify(xk_closed.subs({k: 1})) == 2

def test_diff_eq_ex218():
    """
    Ogata Ex. 2-18:
      x(k+2) + 3 x(k+1) + 2 x(k) = 0,  x(0)=0, x(1)=1
      Solution: x[k] = (-1)^k - (-2)^k
      First terms: 0, 1, -3, 7, -15, 31, ...
    """
    syms = symbol_table()
    a0, a1, a2 = 1, 3, 2
    ics = {sp.Function('x')(0): 0, sp.Function('x')(1): 1}
    eq, sol, seq = core.solve_difference([a0, a1, a2], None, ics, syms, N=6)

    # sequence check (first 6 samples)
    assert [int(sp.N(v)) for v in seq[:6]] == [0, 1, -3, 7, -15, 31]

    # closed-form identity check at a few k
    k = syms["k"]
    xk_expected = (-1)**k - (-2)**k
    for ki in range(0, 6):
        lhs = sp.simplify(sol.subs({k: ki}))
        rhs = sp.simplify(xk_expected.subs({k: ki}))
        assert sp.simplify(lhs - rhs) == 0
