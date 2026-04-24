from __future__ import annotations
import sympy as sp
from state_space.stateConverterTool.apis import RunRequest, RunResult

def test_dataclasses_init_and_repr():
    A = sp.eye(1); B = sp.ones(1,1); C = sp.ones(1,1); D = sp.zeros(1,1); T = sp.Symbol('T', positive=True)
    req = RunRequest(A=A,B=B,C=C,D=D,T=T, example=None, digits=7, evalf=12, simplify=False, force_inverse=True, allow_singular_fallback=False, want_latex=True, latex_out="out/x.tex")
    assert req.digits == 7 and req.evalf == 12 and req.force_inverse and req.want_latex
    res = RunResult(G=sp.eye(1), H=sp.zeros(1,1), F=sp.ones(1,1), Finv=None, latex="ok")
    assert res.latex == "ok" and res.F.shape == (1,1)
