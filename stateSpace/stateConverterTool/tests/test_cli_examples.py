from __future__ import annotations
import subprocess, sys, os, json, textwrap, pathlib

PKG_DIR = pathlib.Path(__file__).resolve().parents[1]

def run_cli(args):
    cmd = [sys.executable, str(PKG_DIR / "cli.py"), *args]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(PKG_DIR))

def test_cli_help_runs():
    res = run_cli(["--help"])
    assert res.returncode == 0
    assert "ZOH discretization" in res.stdout

def test_cli_example_runs_matlab_p318():
    res = run_cli(["--example","matlab_p318","--evalf","16"])
    assert res.returncode == 0
    assert "F(z)" in res.stdout
