from __future__ import annotations
import subprocess, sys, pathlib

PKG_DIR = pathlib.Path(__file__).resolve().parents[1]

def run_cli(args):
    cmd = [sys.executable, str(PKG_DIR / "cli.py"), *args]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(PKG_DIR))

def test_cli_singular_A_no_fallback_exits_cleanly():
    res = run_cli([
        "--A","[[0,1],[0,0]]",
        "--B","[[0],[1]]",
        "--C","[[1,0]]",
        "--D","[[0]]",
        "--T","1",
        "--no-fallback"
    ])
    assert res.returncode == 2
    assert "Singular A detected and --no-fallback was used" in res.stderr
