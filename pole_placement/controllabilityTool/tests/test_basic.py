from __future__ import annotations
import json, os, sys
import numpy as np

# Import shim for tests when run from repo root or inside package
pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if pkg_root not in sys.path:
    sys.path.insert(0, pkg_root)

from pole_placement.controllabilityTool.app import ControllabilityApp
from pole_placement.controllabilityTool.apis import RunRequest

def test_ctrb_rank_full():
    app = ControllabilityApp()
    req = RunRequest(A="0 1; -2 -3", B="0; 1", pretty=False, name="t_full", save_json=True)
    res = app.run(req)
    assert res.exit_code == 0
    out_json = os.path.join(os.path.dirname(__file__), "..", "out", "t_full_summary.json")
    assert os.path.exists(out_json)
    data = json.load(open(out_json))
    assert data["rank_ctrb"] == 2
    assert data["full_ctrb_rank_n"] is True

def test_output_controllability_matrix():
    app = ControllabilityApp()
    req = RunRequest(A="0 1; -2 -3", B="0; 1", C="1 0", output_ctrb=True, save_output_csv=True, name="t_out")
    res = app.run(req)
    assert res.exit_code in (0,2)  # rank may or may not be full depending on C; we only check file
    csv_path = os.path.join(os.path.dirname(__file__), "..", "out", "t_out_outctrb.csv")
    assert os.path.exists(csv_path)
