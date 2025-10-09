
from __future__ import annotations
import json, os, tempfile
import numpy as np

from polePlacement.transformationTool.io import parse_matrix, load_from_json
from polePlacement.transformationTool import utils

def test_parse_matrix_happy_and_edge():
    assert parse_matrix(None) is None
    assert parse_matrix("   ") is None
    M = parse_matrix("1 2; 3 4")
    assert M.shape == (2,2)
    assert np.allclose(M.astype(float), [[1,2],[3,4]])
    # complex entries and commas
    Mc = parse_matrix("1, 2j; -3, 4")
    assert Mc.shape == (2,2)
    assert Mc[0,1] == 2j

def test_parse_matrix_bad_cols():
    import pytest
    with pytest.raises(ValueError):
        parse_matrix("1 2; 3 4 5")

def test_load_from_json_tmpfile(tmp_path):
    p = tmp_path / "sys.json"
    data = {"A": [[0,1],[-2,-3]], "B": [[0],[1]], "C": [[1,0]], "D": [[0]]}
    p.write_text(json.dumps(data))
    A,B,C,D = load_from_json(str(p))
    assert A.shape == (2,2) and B.shape == (2,1) and C.shape == (1,2) and D.shape == (1,1)

def test_utils_numpy_json_and_dump_csv_json(tmp_path, monkeypatch):
    # route output to a temp dir
    monkeypatch.setattr(utils, "OUTDIR", str(tmp_path))
    utils.ensure_outdir()

    obj = {"x": np.array([[1,2],[3,4]]), "c": 1+0j, "z": 1+2j}
    enc = utils.numpy_json(obj)
    assert enc["x"] == [[1,2],[3,4]]
    assert enc["c"] == 1.0 and isinstance(enc["z"], dict)

    utils.dump_json({"A": np.array([[1]])}, "tiny")
    assert (tmp_path / "tiny.json").exists()

    # CSV bundle
    utils.save_csv_bundle({"A": np.array([[1,2],[3,4]])}, "bundle")
    assert (tmp_path / "bundle_A.csv").exists()

def test_pretty_mat_formats():
    from polePlacement.transformationTool.utils import pretty_mat
    M = np.array([[1.0, 2.0],[3.0, 4.0]])
    s = pretty_mat(M)
    assert "1.000000" in s and "\n" in s
