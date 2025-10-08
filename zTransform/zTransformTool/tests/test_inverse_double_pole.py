# -*- coding: utf-8 -*-
import sympy as sp
from zTransform.zTransformTool import core
from zTransform.zTransformTool.utils import symbol_table


def _header(title: str):
    print("\n" + "=" * len(title))
    print(title)
    print("=" * len(title))


def test_inverse_double_pole_case_b7():
    """
    NOISY DEBUG TEST
    B7: X(z) = z^2 / ((z - 1)^2 * (z - e^{-aT})) with a=1, T=1.
    We print the whole pipeline: X(z) -> X(u) -> A(u),B(u) -> h[k] -> x[k] and the
    finite sequence from recurrence, then compare sample-by-sample.
    """
    syms = symbol_table()
    k, a, T, z = syms["k"], syms["a"], syms["T"], syms["z"]
    X = "z**2/((z-1)**2*(z-exp(-a*T)))"
    subs = {a: 1, T: 1}

    _header("SETUP")
    print(f"X(z)   = {X}")
    print(f"subs   = { {str(s): float(v) for s, v in subs.items()} }")
    print("N      = 6")

    # Invert via our public API (unilateral path + closed-form)
    xk_closed, seq = core.inverse_z(X, syms, N=6, subs={"a": 1, "T": 1})

    assert seq is not None and len(seq) == 7, "Expected 7 samples (0..6) from core.inverse_z"
    assert xk_closed is not None, "Closed-form should not be None"

    _header("CLOSED FORM x[k] (symbolic)")
    print(sp.simplify(xk_closed))

    _header("CLOSED FORM x[k] with subs a=1, T=1")
    print(sp.simplify(xk_closed.subs(subs)))

    _header("SEQUENCE x[0..6] FROM RECURRENCE")
    print([sp.simplify(s) for s in seq])

    # Drill into internal building blocks for more visibility
    _header("INTERNALS: X(u), A(u), B(u), deg(A)")
    XZ = sp.apart(sp.simplify(sp.sympify(X, locals=syms)), z)
    u, Xu = core.Xu_from_Xz(XZ, z)
    A, B = core.rational_AB_in_u(Xu, u)
    print(f"X(u)   = {sp.simplify(Xu)}")
    print(f"A(u)   = {A.as_expr()}  ; deg(A)={A.degree()}")
    print(f"B(u)   = {B.as_expr()}")

    # Show the impulse response closed form h[k]
    if A.degree() > 0:
        h_closed = core.impulse_response_closed(A, k)
        _header("IMPULSE RESPONSE h[k] of H(u)=1/A(u)")
        print("h[k] (symbolic)        =", sp.simplify(h_closed))
        print("h[k] (with a=1,T=1)    =", sp.simplify(h_closed.subs(subs)))
    else:
        print("A(u) is degree 0 -> h[k] is trivial delta-sequence")

    # Numeric compare table
    _header("COMPARE CLOSED-FORM vs SEQ (k, closed_form, seq, diff)")
    max_abs_diff = 0.0
    for i in range(7):
        lhs = sp.N(sp.simplify(xk_closed.subs({k: i, **subs})))
        rhs = sp.N(sp.simplify(seq[i]))
        diff = float(lhs - rhs)
        max_abs_diff = max(max_abs_diff, abs(diff))
        print(f"k={i:2d} | closed={lhs} | seq={rhs} | diff={diff:+.12g}")

    # If it fails, we want the huge print above to accompany the assertion message
    assert max_abs_diff < 1e-9, f"Max |closed - seq| = {max_abs_diff} (see noisy dump above)"

    # structural sanity (not strict, just ensure k is present)
    expr_str = str(sp.simplify(xk_closed.subs(subs)))
    assert "k" in expr_str
