import os
import sympy as sp
from stateSpace.liapunovTool.apis import RunRequest
from stateSpace.liapunovTool.app import LyapunovApp

def test_app_ct_real_latex(tmp_path):
    app = LyapunovApp()
    out_tex = tmp_path / "ct_block.tex"
    req = RunRequest(
        mode="ct",
        A="[[0 1]; [-25 -4]]",
        Q="[[1 0]; [0 1]]",
        digits=8,
        evalf=12,
        latex=True,
        latex_out=str(out_tex),
    )
    res = app.run(req)
    assert res.mode == "ct"
    assert (out_tex).exists()
    assert "Continuous-time Lyapunov" in (out_tex).read_text()

def test_app_dt_hermitian_evalf_and_relative_out():
    app = LyapunovApp()
    # relative latex_out -> should be written under default out dir
    req = RunRequest(
        mode="dt",
        G="[[0, 1+i]; [-(1-i), -2]]",
        Q="[[1 0]; [0 1]]",
        hermitian=True,
        evalf=16,
        latex=True,
        latex_out="herm_dt.tex",
    )
    res = app.run(req)
    # Hermitian result should satisfy P == P.H (within sympy semantics)
    assert res.P.H == res.P
    # file should land in default out folder
    assert os.path.exists("stateSpace/liapunovTool/out/herm_dt.tex")
