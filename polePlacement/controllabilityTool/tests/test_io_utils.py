
from __future__ import annotations
import os, json, pytest, numpy as np

from polePlacement.controllabilityTool.io import parse_matrix_string, load_from_json
from polePlacement.controllabilityTool.utils import stable_ct, stable_dt, rank_numeric, real_if_close_for_control

def test_parse_matrix_string_ok():
    M = parse_matrix_string("1 2; 3 4")
    assert M.shape == (2,2)
    assert M.dtype.kind in ("c","f")

def test_parse_matrix_string_bad():
    with pytest.raises(ValueError):
        parse_matrix_string("1 2; 3")

def test_load_from_json_ok(tmp_path):
    p = tmp_path / "ct_demo.json"
    json.dump({"A": [[0,1],[-2,-3]], "B": [[0],[1]], "discrete": False}, open(p,"w"))
    A,B,disc,C,D = load_from_json(str(p))
    assert A.shape==(2,2) and B.shape==(2,1) and disc is False and C is None and D is None

def test_load_from_json_missing(tmp_path):
    p = tmp_path / "bad.json"
    json.dump({"A": [[1,0],[0,1]]}, open(p,"w"))
    with pytest.raises(ValueError):
        load_from_json(str(p))

def test_utils_stability_and_rank():
    A = np.array([[0,1],[-2,-3]], dtype=float)
    assert stable_ct(A) is True
    Ad = np.array([[0.9, 0.0],[0.0, 0.8]])
    assert stable_dt(Ad) is True
    r = rank_numeric(np.eye(3))
    assert r == 3
    Z = np.array([[1e-13]])
    assert rank_numeric(Z) in (0,1)
    X = np.array([[1+1e-14j]])
    Y = real_if_close_for_control(X)
    assert isinstance(Y, np.ndarray)
