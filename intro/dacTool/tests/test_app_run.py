
from __future__ import annotations
from intro.dacTool.app import run
from intro.dacTool.apis import RunRequest

def test_app_run_weighted_json(tmp_path):
    req = RunRequest(
        dac_type="weighted", nbits=3, vref=2.5, ro_over_r=1.0,
        jspec="[0,1,2,3]", out_dir=str(tmp_path), out_csv="w.csv", out_vcd="w.vcd",
        include_ideal_in_vcd=True
    )
    res = run(req)
    assert (tmp_path / "w.csv").exists()
    assert (tmp_path / "w.vcd").exists()
    assert len(res.rows) == 4

def test_app_run_r2r_csv(tmp_path):
    # Create CSV
    f = tmp_path / "in.csv"; f.write_text("code\n0\n1\n3\n")
    req = RunRequest(
        dac_type="r2r", nbits=2, vref=3.3, R_ohm=10000.0,
        csv=str(f), out_dir=str(tmp_path), out_csv="r.csv", out_vcd="r.vcd"
    )
    res = run(req)
    assert (tmp_path / "r.csv").exists()
    assert (tmp_path / "r.vcd").exists()
    assert len(res.rows) == 3
