from __future__ import annotations
import subprocess, sys, pathlib

PKG_DIR = pathlib.Path(__file__).resolve().parents[1]

def run_cli(args):
    cmd = [sys.executable, str(PKG_DIR / "cli.py"), *args]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(PKG_DIR))

def test_cli_force_inverse_and_no_simplify_paths():
    res = run_cli([
        "--A","[[0,1],[-25,-4]]",
        "--B","[[0],[1]]",
        "--C","[[1,0]]",
        "--D","[[0]]",
        "--T","0.05",
        "--evalf","12",
        "--force-inverse",
        "--no-simplify"
    ])
    assert res.returncode == 0
    # should include inverse print and F(z)
    assert "(zI - G)^(-1)" in res.stdout
    assert "F(z)" in res.stdout
