# -*- coding: utf-8 -*-
import sys, subprocess, pathlib, json

PKG_DIR = pathlib.Path(__file__).resolve().parents[1]

def _run_cli(args, tmp_path):
    cmd = [sys.executable, "cli.py"] + args
    p = subprocess.run(cmd, cwd=PKG_DIR, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr + "\n" + p.stdout
    return p

def test_cli_lead_and_manifest(tmp_path):
    out = tmp_path / "out"
    _run_cli([
        "--T","0.2",
        "--gz-num","0.01873, 0.01752",
        "--gz-den","1, -1.8187, 0.8187",
        "--comp","lead","--K","1.0","--alpha","0.361","--tau","0.979",
        "--plot","plotly","--plotly-output","html",
        "--step","15",
        "--out", str(out)
    ], tmp_path)
    mf = out / "manifest.json"
    data = json.loads(mf.read_text())
    assert "Gd_z_num_desc" in data and "files" in data

def test_cli_auto(tmp_path):
    out = tmp_path / "out"
    _run_cli([
        "--T","0.2",
        "--gz-num","0.01873, 0.01752",
        "--gz-den","1, -1.8187, 0.8187",
        "--comp","auto","--pm","50","--gm","10","--Kv","2",
        "--out", str(out)
    ], tmp_path)
    assert (out / "manifest.json").exists()
