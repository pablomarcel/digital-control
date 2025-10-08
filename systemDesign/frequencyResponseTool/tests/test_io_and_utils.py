# -*- coding: utf-8 -*-
import os, json, time

from systemDesign.frequencyResponseTool.io import parse_desc_list, write_manifest
from systemDesign.frequencyResponseTool.utils import log_call, timer, poly_mul_desc, poly_add_desc, ensure_dir

def test_parse_and_manifest(tmp_path):
    assert parse_desc_list("1, 2,3") == [1.0,2.0,3.0]
    assert parse_desc_list([4,5]) == [4.0,5.0]
    path = write_manifest(str(tmp_path), {"a":1})
    assert os.path.exists(path)

def test_utils_decorators_and_polys(tmp_path):
    calls = {"n":0}
    @log_call("unit")
    @timer
    def f(x): 
        calls["n"] += 1
        return x + 1
    y = f(2)
    assert y == 3 and calls["n"] == 1

    p = poly_mul_desc([1,1], [1,-1])   # (s+1)(s-1) = s^2 - 1
    assert p == [1.0, 0.0, -1.0]

    q = poly_add_desc([1,0,-1],[1,2,3])  # s^2-1 + s^2+2s+3 = 2s^2+2s+2
    assert q == [2.0, 2.0, 2.0]

    d = tmp_path / "x/y"
    ensure_dir(str(d))
    assert os.path.isdir(d)
