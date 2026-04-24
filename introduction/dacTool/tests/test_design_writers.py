
from __future__ import annotations
import os, pathlib
from introduction.dacTool.design import write_results_csv, write_vcd
from introduction.dacTool.apis import Update

def test_write_results_and_vcd(tmp_path):
    rows = [
        {"nbits":3,"vref":2.5,"R_ohm":10000,"sigma_r_pct":0.1,"sigma_2r_pct":0.2,
         "ro_over_r":"","res_sigma_pct":"","code":5,"vo_ideal":1.0,"vo_nonideal":1.1,
         "error":0.1,"gain_err":0.0,"vo_offset":0.0}
    ]
    csvp = tmp_path / "res.csv"
    write_results_csv(str(csvp), rows)
    assert csvp.exists() and csvp.read_text().splitlines()[0].startswith("index,nbits")

    vcdf = tmp_path / "trace.vcd"
    _ = write_vcd(str(vcdf), 3, [Update(code=5, vo_ideal=1.0, vo_nonideal=1.1)], tupd=1e-6,
                  include_ideal=True)
    content = vcdf.read_text()
    assert "$var wire 32 vi voi_uV $end" in content
