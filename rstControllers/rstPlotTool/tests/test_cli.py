
from __future__ import annotations
import os, sys
from rstControllers.rstPlotTool.cli import main as cli_main
from rstControllers.rstPlotTool import utils

def test_cli_end_to_end(tmp_path, monkeypatch):
    # Redirect package OUT_DIR to tmp
    monkeypatch.setattr(utils, "OUT_DIR", str(tmp_path))

    # Prepare a csv next to tmp
    p = tmp_path / "c.csv"
    with open(p, "w") as f:
        f.write("k,r,y,u,v\n0,0,0,0,0\n1,1,0.6,0.2,0\n2,1,0.9,0.1,0\n")
    # Run CLI: single, mpl only
    code = cli_main([str(p), "--backend", "mpl"])
    assert code == 0
    # stem of c.csv is c
    assert (tmp_path / "c_mpl.png").exists()
