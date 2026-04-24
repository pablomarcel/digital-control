from __future__ import annotations
import json, pytest, tempfile, os
from introduction.zohTool.io import load_u_from_json, load_u_from_csv

def test_bad_json_raises():
    with pytest.raises(ValueError):
        load_u_from_json('{"not":"expected"}')

def test_csv_missing_u_raises(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("x\n1\n")
    with pytest.raises(ValueError):
        load_u_from_csv(str(p))
