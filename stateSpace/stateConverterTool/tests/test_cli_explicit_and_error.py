from __future__ import annotations
import subprocess, sys, pathlib

PKG_DIR = pathlib.Path(__file__).resolve().parents[1]

def run_cli(args, cwd=PKG_DIR):
    cmd = [sys.executable, str(PKG_DIR / "cli.py"), *args]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd))

def test_cli_full_args_runs_tmpdir(tmp_path):
    # run with explicit matrices and latex out
    out_tex = tmp_path / "out" / "demo.tex"
    res = run_cli([
        "--A","[[0,1],[-25,-4]]",
        "--B","[[0],[1]]",
        "--C","[[1,0]]",
        "--D","[[0]]",
        "--T","0.05",
        "--evalf","12",
        "--latex","--latex-out", str(out_tex)
    ])
    assert res.returncode == 0
    assert "F(z)" in res.stdout
    assert out_tex.exists()

def test_cli_missing_args_errors():
    res = run_cli(["--A","[[1]]"])
    assert res.returncode != 0
    assert "Missing required arguments" in res.stderr or "usage:" in res.stderr
