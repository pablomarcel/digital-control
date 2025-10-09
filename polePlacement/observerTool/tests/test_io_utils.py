from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from pathlib import Path

from polePlacement.observerTool.io import parse_matrix, parse_poles, load_yaml, maybe_json
from polePlacement.observerTool.utils import asjson, to_jsonable, eigvals_sorted, multiset_close, out_path, save_csv_matrix, save_csv_series, save_json

def test_parse_matrix_variants_and_poles(tmp_path):
    assert np.allclose(parse_matrix('1 2; 3 4'), np.array([[1,2],[3,4]]))
    assert np.allclose(parse_matrix([[1,2],[3,4]]), np.array([[1,2],[3,4]]))
    assert np.allclose(parse_matrix('1;2;3'), np.array([[1],[2],[3]]))
    assert np.allclose(parse_matrix('1 2 3'), np.array([[1,2,3]]))
    ps = parse_poles('0.5+0.2j,0.5-0.2j,0')
    assert len(ps) == 3 and ps[0] == complex('0.5+0.2j')
    # yaml
    yml = tmp_path / "cfg.yaml"
    yml.write_text("plant:\n  A: [[1,0],[0,1]]\n")
    y = load_yaml(yml)
    assert "plant" in y
    # maybe_json
    assert maybe_json("[1,2,3]") == [1,2,3]
    assert maybe_json("{\"a\":1}") == {"a":1}
    assert maybe_json("not_json") == "not_json"

def test_utils_json_and_savers(tmp_path):
    class Obj:
        def __init__(self): self.x = 1
    data = {"a": np.array([1.0, 2.0]), "b": 3+0j}
    s = asjson(data)
    assert '"a": [\n    1.0,\n    2.0\n  ]' in s
    # out_path with bare filename goes to package ./out (simulate by writing then checking parent name)
    p = out_path("hello.json")
    save_json(p, {"hi": 1})
    assert p.exists()
    # csv matrix & series
    cm = tmp_path / "m.csv"
    cs = tmp_path / "s.csv"
    save_csv_matrix(cm, np.array([[1,2],[3,4]]), header=["M"])
    save_csv_series(cs, {"t":[0,1], "y":[1.0,2.0]})
    assert cm.exists() and cs.exists()
    # eigen helpers
    A = np.eye(2)
    e = eigvals_sorted(A)
    assert len(e) == 2
    assert multiset_close([1,1], [1+0j,1-0j])
