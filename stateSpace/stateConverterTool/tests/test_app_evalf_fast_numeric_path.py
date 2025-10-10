from __future__ import annotations
import sympy as sp
from stateSpace.stateConverterTool.apis import RunRequest
from stateSpace.stateConverterTool.app import StateConverterApp

def test_app_evalf_fast_numeric_path_produces_floats():
    # all numeric inputs + evalf should produce Float entries
    A = sp.Matrix([[0,1],[-25,-4]])
    B = sp.Matrix([[0],[1]])
    C = sp.Matrix([[1,0]])
    D = sp.Matrix([[0]])
    T = sp.Rational(1,20)
    req = RunRequest(A=A,B=B,C=C,D=D,T=T, evalf=12, simplify=True)
    res = StateConverterApp().run(req)
    # Check G entries are Float-like (at least one is Float)
    assert any(isinstance(x, sp.Float) for x in res.G)
