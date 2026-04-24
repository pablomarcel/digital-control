
from __future__ import annotations
import os, numpy as np
from rst_controllers.rstPlotTool import design, utils

def _fake_data(n=10):
    k = np.arange(n, dtype=float)
    r = np.ones(n, dtype=float)
    y = r - np.exp(-0.5*k/ (n/5.0))
    u = 0.2*np.ones(n, dtype=float)
    v = np.zeros(n, dtype=float)
    e = r - y
    return dict(k=k,r=r,y=y,u=u,v=v,e=e)

def test_mpl_single_and_overlay(tmp_path, monkeypatch):
    # direct outputs to a temp OUT_DIR
    monkeypatch.setattr(utils, "OUT_DIR", str(tmp_path))
    d = _fake_data(30)
    design.mpl_single("single.png", d, "T", "matlab", 120, (None, None, None), annotate=None)
    assert (tmp_path / "single.png").exists()

    d2 = _fake_data(30)
    files = ["a.csv", "b.csv"]
    design.mpl_overlay("overlay.png", files, [d, d2], "light", 120,
                       legend_mode="full", robust=0.99,
                       ylims=((0,1.1), (-1,1), (-0.2,1.0)), clip_to_limits=True, title="X")
    assert (tmp_path / "overlay.png").exists()
