from __future__ import annotations
import sympy as sp
from stateSpace.stateConverterTool.core import StateConverterCore

def test_force_inverse_branch_and_simplification():
    A = sp.Matrix([[0, 1],
                   [-25, -4]])
    B = sp.Matrix([[0],[1]])
    C = sp.Matrix([[1, 0]])
    D = sp.Matrix([[0]])
    T = sp.Rational(1,20)
    core = StateConverterCore(simplify=True)
    G = core.compute_G(A, T)
    H = core.compute_H(A, G, B, T)
    Finv, F = core.compute_F(G, H, C, D, force_inverse=True)
    assert Finv is not None
    # F should be rational function in z
    z = sp.symbols('z')
    assert z in F[0,0].free_symbols
