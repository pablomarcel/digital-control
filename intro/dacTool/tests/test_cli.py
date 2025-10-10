from __future__ import annotations
import os, subprocess, sys, json, pathlib

def test_cli_weighted_runs(tmp_path):
    pkg_dir = pathlib.Path(__file__).resolve().parents[1]
    cli = pkg_dir / "cli.py"
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()
    out_dir.mkdir()
    # prepare CSV
    (in_dir / "codes.csv").write_text("code\n0\n1\n2\n3\n")
    cmd = [sys.executable, str(cli), "weighted",
           "--csv", "codes.csv",
           "--nbits", "3", "--vref", "2.5", "--gain", "1.0",
           "--in-dir", str(in_dir),
           "--out-dir", str(out_dir),
           "--out", "res.csv",
           "--trace", "w.vcd",
           "--vcd-ideal"]
    subprocess.run(cmd, check=True, cwd=str(pkg_dir))
    assert (out_dir / "res.csv").exists()
    assert (out_dir / "w.vcd").exists()

def test_cli_r2r_runs(tmp_path):
    pkg_dir = pathlib.Path(__file__).resolve().parents[1]
    cli = pkg_dir / "cli.py"
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()
    out_dir.mkdir()
    (in_dir / "codes.csv").write_text("code\n0\n5\n7\n")
    cmd = [sys.executable, str(cli), "r2r",
           "--csv", "codes.csv",
           "--nbits", "3", "--vref", "3.3", "--R", "10000",
           "--in-dir", str(in_dir),
           "--out-dir", str(out_dir),
           "--out", "res.csv",
           "--trace", "r.vcd"]
    subprocess.run(cmd, check=True, cwd=str(pkg_dir))
    assert (out_dir / "res.csv").exists()
    assert (out_dir / "r.vcd").exists()
