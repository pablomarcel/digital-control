
from __future__ import annotations
import os, json, glob
from rstControllers.rstPlotTool import io

def test_expand_files_and_design_json(tmp_path):
    a = tmp_path / 'a.csv'
    b = tmp_path / 'b.csv'
    a.write_text('k,r,y,u,v\n0,0,0,0,0\n')
    b.write_text('k,r,y,u,v\n0,0,0,0,0\n')

    pats = io.expand_files([str(tmp_path / '*.csv')])
    assert len(pats) == 2 and all(p.endswith('.csv') for p in pats)

    j = tmp_path / 'd.json'
    j.write_text(json.dumps({"plant":{"A":[1], "B":[1], "d":0}, "controller":{"R":[1],"S":[1],"T":[1]}, "target":{"Acl":[1]}}))
    data = io.load_design_json(str(j))
    assert data["plant"]["d"] == 0

    # Missing returns None
    assert io.load_design_json(str(tmp_path/'missing.json')) is None
