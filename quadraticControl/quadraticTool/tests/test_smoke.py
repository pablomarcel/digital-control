import os, numpy as np
from quadraticControl.quadraticTool.apis import RunRequest
from quadraticControl.quadraticTool.app import QuadraticApp
from quadraticControl.quadraticTool.utils import pkg_path

def test_fh_dt_smoke(tmp_path):
    infile = pkg_path("in","ex8_1.yaml")
    outdir = str(tmp_path / "out")
    req = RunRequest(mode="fh-dt", infile=infile, name="ex1", outdir=outdir, plot="none")
    case_dir = QuadraticApp().run(req)
    assert os.path.isdir(case_dir)
    # sanity: K, x, u files exist
    for fname in ["K.csv","x.csv","u.csv","summary.txt"]:
        assert os.path.exists(os.path.join(case_dir, fname))

def test_ss_lqr_shapes():
    # trivial 1x1 stable plant; shapes sanity
    G = np.array([[0.9]]); H = np.array([[0.1]])
    Q = np.array([[1.0]]); R = np.array([[0.5]])
    from quadraticControl.quadraticTool.core import SteadyStateLQR
    res = SteadyStateLQR().solve(G,H,Q,R)
    assert res.P.shape == (1,1) and res.K.shape == (1,1)
