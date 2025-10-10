
import os, io
import contextlib
from stateSpace.stateSolverTool import cli

def cd_pkg_dir():
    import stateSpace.stateSolverTool as pkg
    return os.path.dirname(pkg.__file__)

def run_and_capture(args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cli.main(args)
    return buf.getvalue()

def test_cli_example_runs_and_prints():
    out = run_and_capture(["--example", "ogata_5_2"])
    assert "LTI system" in out and "Psi(k)" in out

def test_cli_ltv_runs_and_prints():
    out = run_and_capture([
        "--mode","ltv",
        "--Gk","[[1,1],[0,1]]",
        "--Hk","[[0],[0]]",
        "--Ck","[[1,0]]",
        "--Dk","[[0]]",
        "--x0","[0,0]",
        "--u","0",
        "--steps","2"
    ])
    assert "LTV system" in out and "Phi" in out
