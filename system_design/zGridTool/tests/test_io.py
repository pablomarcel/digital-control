
# -*- coding: utf-8 -*-
from __future__ import annotations
import json, csv
from pathlib import Path
from system_design.zGridTool.io import read_pz_json, read_pz_csv, PZ

def test_read_pz_json_all_forms(tmp_path):
    data = {
        "poles": ["0.7+0.1j", {"re": 0.5, "im": -0.2, "label": "p1"}],
        "zeros": [[0.3, 0.0], {"re": 0.2, "im": 0.1}]
    }
    p = tmp_path / "pz.json"
    p.write_text(json.dumps(data))
    pzs = read_pz_json(p)
    assert len(pzs) == 4
    kinds = {pz.kind for pz in pzs}
    assert kinds == {"pole","zero"}

def test_read_pz_csv_variants(tmp_path):
    # 1) has columns re,im,label,kind
    p1 = tmp_path / "a.csv"
    p1.write_text("re,im,label,kind\n0.5,0.0,z1,zero\n0.8,0.2,p1,pole\n")
    pzs1 = read_pz_csv(p1)
    assert len(pzs1) == 2 and {pz.kind for pz in pzs1} == {"pole","zero"}

    # 2) has combined complex column z plus type alias
    p2 = tmp_path / "b.csv"
    p2.write_text("z,type,name\n0.6+0.1j,zero,z2\n0.9-0.1j,pole,p2\n")
    pzs2 = read_pz_csv(p2)
    assert len(pzs2) == 2 and {pz.kind for pz in pzs2} == {"pole","zero"}
