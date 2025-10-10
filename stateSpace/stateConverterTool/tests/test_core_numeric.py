from __future__ import annotations
import sympy as sp
from stateSpace.stateConverterTool.core import StateConverterCore

def test_numeric_expm_and_H_matches_linear_solve():
    A = sp.Matrix([[0, 1],
                   [-25, -4]])
    B = sp.Matrix([[0],[1]])
    T = sp.Rational(5,100)  # 0.05
    core = StateConverterCore(simplify=True)
    G = core.compute_G(A, T)
    H = core.compute_H(A, G, B, T)

    # Basic shape checks
    assert G.shape == (2,2)
    assert H.shape == (2,1)

    # sanity: discrete pair should be finite numbers
    assert all(e.is_finite for e in G)
    assert all(e.is_finite for e in H)

def test_pulse_tf_siso_shape():
    A = sp.Matrix([[0, 1],
                   [-25, -4]])
    B = sp.Matrix([[0],[1]])
    C = sp.Matrix([[1, 0]])
    D = sp.Matrix([[0]])
    T = sp.Rational(5,100)
    core = StateConverterCore(simplify=True)
    G = core.compute_G(A, T)
    H = core.compute_H(A, G, B, T)
    Finv, F = core.compute_F(G, H, C, D, force_inverse=False)

    assert F.shape == (1,1)
    z = sp.symbols('z')
    assert F[0,0].free_symbols.issuperset({z})
