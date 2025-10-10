
import os, sympy as sp
from stateSpace.stateSolverTool.app import StateSolverApp
from stateSpace.stateSolverTool.apis import RunRequest

def pkg_dir():
    import stateSpace.stateSolverTool as pkg
    return os.path.dirname(pkg.__file__)

def test_app_ltv_branch_runs():
    app = StateSolverApp(pkg_dir=pkg_dir())
    req = RunRequest(
        mode="ltv",
        Gk="[[1,1],[0,1]]",
        Hk="[[0],[0]]",
        Ck="[[1,0]]",
        Dk="[[0]]",
        x0="[0,0]",
        u="0",
        steps=3,
    )
    res = app.run(req)
    assert res.mode == "ltv" and res.ltv.Phi.shape == (2,2) and res.ltv.check_status == "ok."

def test_app_lti_latex_out_relative_path(tmp_path):
    app = StateSolverApp(pkg_dir=pkg_dir())
    req = RunRequest(
        mode="lti",
        G="[[0,1],[-0.16,-1]]",
        H="[[1],[1]]",
        C="[[1,0]]",
        D="[[0]]",
        x0="[1,-1]",
        u="1",
        latex=True,
        zt=True,
        latex_out="unit_test_out.tex",
        check="off"
    )
    res = app.run(req)
    # file should be placed under package out/
    out_path = os.path.join(pkg_dir(), "out", "unit_test_out.tex")
    assert os.path.exists(out_path)
