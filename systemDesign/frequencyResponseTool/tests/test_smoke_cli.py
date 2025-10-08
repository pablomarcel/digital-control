# -*- coding: utf-8 -*-
import os, subprocess, sys, json, pathlib

PKG_DIR = pathlib.Path(__file__).resolve().parents[1]

def test_cli_smoke(tmp_path):
    # run inside the package directory via import shim
    cwd = PKG_DIR
    out = tmp_path / "out"
    cmd = [
        sys.executable, "cli.py",
        "--T", "0.2",
        "--gz-num", "0.01873, 0.01752",
        "--gz-den", "1, -1.8187, 0.8187",
        "--comp", "none",
        "--plot", "plotly",
        "--plotly-output", "html",
        "--out", str(out)
    ]
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr + "\n" + p.stdout
    mf = out / "manifest.json"
    assert mf.exists()
    data = json.loads(mf.read_text())
    assert "files" in data
