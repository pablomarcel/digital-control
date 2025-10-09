
import json
import pathlib
import pytest
import numpy as np

from polePlacement.observabilityTool.design import capture_pretty_text
from polePlacement.observabilityTool.io import parse_matrix_string, load_from_json, save_json
from polePlacement.observabilityTool.utils import pkg_outdir

def test_capture_pretty_text():
    txt = capture_pretty_text(
        discrete=False, n=2, m=1, eigvals=[-1+0j, -2+0j],
        Obsv=np.array([[1,0],[0,1]], dtype=complex),
        rank=2, full=True, sym_rank=2,
        pbh_details=[{"lambda": -1+0j, "rank":2, "sigma_min":1e-3, "pass": True}],
        gram_used="CT", stability=True, gram_min_eig=1.0, gram_posdef=True,
        W_finite=np.eye(2), finite_used="CT", finite_horizon=5.0, finite_min_eig=1.0,
    )
    assert "Observability" in txt and "rank(Obsv) = 2" in txt

def test_io_parse_and_json(tmp_path):
    # parse_matrix_string
    M = parse_matrix_string("1 0; 0 1")
    assert M.shape == (2,2)
    # ragged should error
    with pytest.raises(ValueError):
        parse_matrix_string("1 0; 0")
    # load_from_json / save_json
    jpath = tmp_path/"sys.json"
    payload = {"A": [[-1,0],[0,-2]], "C": [[1,0]], "discrete": False}
    jpath.write_text(json.dumps(payload))
    from polePlacement.observabilityTool.io import load_from_json
    A, C, disc = load_from_json(str(jpath))
    assert A.shape == (2,2) and C.shape == (1,2) and disc is False
    # save_json writes and is valid JSON
    out = tmp_path/"out.json"
    save_json(str(out), {"ok": True})
    assert json.loads(out.read_text())["ok"] is True

def test_pkg_outdir_exists():
    p = pathlib.Path(pkg_outdir())
    assert p.exists() and p.is_dir()
