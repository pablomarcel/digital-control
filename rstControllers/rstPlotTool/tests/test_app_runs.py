
from __future__ import annotations
import os, json, numpy as np
from rstControllers.rstPlotTool.app import RSTPlotApp
from rstControllers.rstPlotTool.apis import RunRequest, YLimits, OverlayFilters
from rstControllers.rstPlotTool import utils

def _write_csv(p, n=20):
    with open(p, "w") as f:
        f.write("k,r,y,u,v\n")
        for i in range(n):
            f.write(f"{i},1,{min(1.0, i/(n/2))},0.1,0\n")

def test_app_single_and_overlay(tmp_path, monkeypatch):
    # redirect OUT_DIR to tmp
    monkeypatch.setattr(utils, "OUT_DIR", str(tmp_path))

    # create inputs in tmp and call via absolute paths
    a = tmp_path / "a.csv"
    b = tmp_path / "b.csv"
    _write_csv(a, 25)
    _write_csv(b, 25)

    app = RSTPlotApp()

    # Single run, mpl only
    req_single = RunRequest(files=[str(a)], overlay=False, backend="mpl", style="matlab", dpi=100)
    app.run(req_single)
    assert (tmp_path / "a_mpl.png").exists()

    # Overlay run
    req_overlay = RunRequest(files=[str(a), str(b)], overlay=True, backend="mpl", style="dark", dpi=100, legend="compact")
    app.run(req_overlay)
    assert (tmp_path / "plot_overlay_mpl.png").exists()
