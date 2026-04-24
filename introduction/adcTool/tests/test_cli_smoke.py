
import os
from introduction.adcTool.cli import main

def test_cli_counter_smoke(tmp_path, monkeypatch):
    in_dir = tmp_path / "in"; out_dir = tmp_path / "out"
    in_dir.mkdir(); out_dir.mkdir()
    vins = in_dir / "vins.csv"
    vins.write_text("vin\n0.1\n0.2\n")
    argv = [
        "--type","counter",
        "--csv", str(vins),
        "--nbits","4","--vref","1.6","--tclk","1e-6",
        "--in-dir", str(in_dir),
        "--out-dir", str(out_dir),
        "--out","res.csv",
        "--trace","last.vcd",
        "--trace-all","all.vcd"
    ]
    main(argv)
    assert (out_dir / "res.csv").exists()
    assert (out_dir / "last.vcd").exists()
    assert (out_dir / "all.vcd").exists()
