
from __future__ import annotations
import os, json, numpy as np, tempfile

from polePlacement.controllabilityTool.design import fmt_matrix, write_csv, write_json, write_text

def test_design_writers_and_fmt(tmp_path):
    M = np.array([[1.0, 2.0],[3.0, 4.0]])
    s = fmt_matrix(M, width=8, prec=3)
    assert isinstance(s, str) and "1" in s

    csv_p = tmp_path / "m.csv"
    json_p = tmp_path / "o.json"
    txt_p = tmp_path / "r.txt"

    write_csv(str(csv_p), M)
    assert csv_p.exists() and csv_p.read_text().strip() != ""

    write_json(str(json_p), {"a": 1})
    assert json.loads(json_p.read_text())["a"] == 1

    write_text(str(txt_p), "hello")
    assert txt_p.read_text() == "hello"
