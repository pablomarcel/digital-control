
from __future__ import annotations
import json, os, pathlib, tempfile
from introduction.dacTool.io import load_vectors_from_csv, load_vectors_from_json

def test_csv_with_bits(tmp_path):
    p = tmp_path / "bits.csv"
    p.write_text("b0,b1,b2\n1,0,1\n0,1,0\n")
    rows = list(load_vectors_from_csv(str(p), 3))
    assert rows[0]["code"] == (1<<0) | (1<<2)

def test_json_inline_list_and_dict(tmp_path):
    # list of codes
    rows = list(load_vectors_from_json("[0,3,5]", 3))
    assert rows[1]["code"] == 3
    # list of dicts with per-bit
    rows2 = list(load_vectors_from_json(
        json.dumps([{"b0":1,"b1":0,"b2":1},{"b0":0,"b1":1,"b2":0}]), 3))
    assert rows2[0]["code"] == (1<<0) | (1<<2)
