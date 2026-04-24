from __future__ import annotations
import os, io
import sympy as sp
from state_space.stateConverterTool.apis import RunRequest
from state_space.stateConverterTool.app import StateConverterApp

def test_app_runs_example_and_writes_latex(tmp_path):
    latex_out = tmp_path / "out" / "ex.tex"
    req = RunRequest(example="matlab_p318", evalf=10, want_latex=True, latex_out=str(latex_out))
    res = StateConverterApp().run(req)
    assert res.G.shape == (2,2) and res.H.shape == (2,1)
    assert latex_out.exists()
    txt = latex_out.read_text(encoding="utf-8")
    assert "ZOH discretization" in txt or "ZOH" in txt
    assert "F(z)" in txt

def test_app_runs_manual_inputs_force_inverse_and_simplify():
    A = sp.Matrix([[0,1],[-25,-4]])
    B = sp.Matrix([[0],[1]])
    C = sp.Matrix([[1,0]])
    D = sp.Matrix([[0]])
    T = sp.Rational(1,20)  # 0.05
    req = RunRequest(A=A,B=B,C=C,D=D,T=T, force_inverse=True, simplify=True)
    res = StateConverterApp().run(req)
    assert res.Finv is not None
    assert res.F.shape == (1,1)

def test_app_singular_fallback_enabled():
    # A is singular (rank 1)
    A = sp.Matrix([[0,1],[0,0]])
    B = sp.Matrix([[0],[1]])
    C = sp.Matrix([[1,0]])
    D = sp.Matrix([[0]])
    T = sp.Integer(1)
    req = RunRequest(A=A,B=B,C=C,D=D,T=T, allow_singular_fallback=True)
    res = StateConverterApp().run(req)
    assert res.H.shape == (2,1)
