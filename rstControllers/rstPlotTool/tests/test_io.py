from __future__ import annotations
from rstControllers.rstPlotTool.io import load_csv

def test_load_csv_roundtrip(tmp_path):
    p = tmp_path / "ex.csv"
    with open(p, "w") as f:
        f.write("k,r,y,u,v\n")
        for i in range(5):
            f.write(f"{i},{1.0},{0.5},{0.1},{0.0}\n")
    d = load_csv(str(p))
    assert set(d.keys()) == {"k","r","y","u","v","e"}
    assert len(d["k"]) == 5 and float(d["e"][-1]) == 0.5
