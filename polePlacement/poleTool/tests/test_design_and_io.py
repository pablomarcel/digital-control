from __future__ import annotations
import json
import numpy as np
from pathlib import Path
from polePlacement.poleTool.design import save_json, save_csv_step, plot_step
from polePlacement.poleTool.io import parse_matrix, parse_poles, load_json_ABC, safeify
from polePlacement.poleTool.utils import ensure_out_dir

def test_parse_and_safeify(tmp_path):
    A = parse_matrix("1 2; 3 4")
    assert A.shape == (2,2)
    poles = parse_poles("0.5+0.2j, 0.5-0.2j", 2)
    assert poles.shape == (2,)
    # JSON loader
    jf = tmp_path / "abc.json"
    jf.write_text(json.dumps({"A": [[1,0],[0,1]], "B": [[0],[1]], "C": [[1,0]]}), encoding="utf-8")
    A2,B2,C2 = load_json_ABC(str(jf))
    assert A2.shape == (2,2) and B2.shape == (2,1) and C2.shape == (1,2)
    # safeify
    obj = {"p": poles, "A": A2}
    s = safeify(obj)
    assert isinstance(s["p"], list) and isinstance(s["A"], list)

def test_plot_and_saves(tmp_path):
    outdir = ensure_out_dir(override=str(tmp_path))
    k = np.arange(10)
    y = np.sin(0.2*np.pi*k)[None,:]
    # csv
    csvp = save_csv_step(k, y, outdir, "case")
    assert csvp.exists()
    # mpl plot
    png = tmp_path / "case_mpl.png"
    plot_step(k, y, "mpl", "dots", png)
    assert png.exists()
    # json
    jp = save_json({"ok": True, "vals":[1,2,3]}, outdir, "case")
    assert jp.exists()
