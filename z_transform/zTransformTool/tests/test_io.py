# -*- coding: utf-8 -*-
import os, json, csv
import sympy as sp
from z_transform.zTransformTool import io as zio
from z_transform.zTransformTool.utils import symbol_table, DEFAULT_OUT_DIR

def test_parse_subs_and_coeffs(tmp_path):
    syms = symbol_table()
    subs = zio.parse_subs("T=0.5,w=2", syms)
    assert syms["T"] in subs and abs(subs[syms["T"]] - 0.5) < 1e-9
    nums = zio.parse_coeffs_numeric("1, -2  3")
    assert nums == [1.0, -2.0, 3.0]
    symc = zio.parse_coeffs_symbolic("a b a+b", syms)
    assert str(symc[2]) in ("a + b","b + a")

def test_export_sequence_writes_files(tmp_path):
    # export with relative names → should land under package out/
    rows = list(range(4))
    vals = [10, 20, 30, 40]
    zio.export_sequence(rows, vals, "v", "seq.csv", "seq.json")

    csv_path = os.path.join(DEFAULT_OUT_DIR, "seq.csv")
    json_path = os.path.join(DEFAULT_OUT_DIR, "seq.json")
    assert os.path.exists(csv_path) and os.path.exists(json_path)

    with open(csv_path) as f:
        r = list(csv.reader(f))
        assert r[0] == ["k","v"]
        # Convert to numeric for robust comparison (writer casts to strings)
        parsed = [(int(k), float(v)) for k, v in r[1:]]
        assert parsed == list(zip(rows, [float(v) for v in vals]))

    with open(json_path) as f:
        obj = json.load(f)
        assert obj["k"] == rows
        # JSON writer keeps numbers numeric — compare as ints/floats
        assert obj["v"] == vals
