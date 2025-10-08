
# -*- coding: utf-8 -*-
from __future__ import annotations
import numpy as np
from pathlib import Path
from systemDesign.zGridTool.design import draw_mpl, Style

def test_draw_mpl_exports(tmp_path):
    fig = draw_mpl(
        T=0.05,
        zetas=[0.2, 0.4],
        wd_over_ws=[0.0, 0.25, 0.5],
        wnT=[0.5, 1.0],
        theta_max=3.141592653589793,
        settling_sigma=1.0,
        pzs=[],
        style=Style(),
        width=600,
        height=600,
        dpi=72,
        dark=False,
        title="unit-test",
        export_prefix=tmp_path / "curves"
    )
    # ensure at least some CSVs were written
    csvs = list(tmp_path.glob("curves_*.csv"))
    assert csvs, "expected one or more exported CSV curve files"
    # basic figure sanity
    assert hasattr(fig, "savefig")
