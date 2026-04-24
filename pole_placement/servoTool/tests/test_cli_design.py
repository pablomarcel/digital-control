from __future__ import annotations
import json, sys
from pole_placement.servoTool.cli import main as cli_main

def run_argv(argv, capsys):
    old = sys.argv[:]
    try:
        sys.argv = argv
        cli_main()
        out = capsys.readouterr().out
        return json.loads(out)
    finally:
        sys.argv = old

def test_cli_design_json(capsys):
    res = run_argv([
        "cli.py", "design",
        "--G","0 1 0; 0 0 1; -0.12 -0.01 1",
        "--H","0;0;1",
        "--C","0.5 1 0",
        "--which","ogata"
    ], capsys)
    assert "K1" in res and "K2" in res

def test_cli_observer_json(capsys):
    res = run_argv([
        "cli.py","observer",
        "--G","0 1 0; 0 0 1; -0.12 -0.01 1",
        "--H","0;0;1",
        "--C","0.5 1 0",
        "--poles","0,0"
    ], capsys)
    assert "Ke" in res and "T" in res

def test_cli_sim_json(capsys):
    # First design to get K1,K2
    dres = run_argv([
        "cli.py","design",
        "--G","0 1 0; 0 0 1; -0.12 -0.01 1",
        "--H","0;0;1",
        "--C","0.5 1 0",
    ], capsys)
    K1 = " ".join(str(v) for v in dres["K1"][0])
    K2 = " ".join(str(v) for v in dres["K2"][0])
    sres = run_argv([
        "cli.py","sim",
        "--G","0 1 0; 0 0 1; -0.12 -0.01 1",
        "--H","0;0;1",
        "--C","0.5 1 0",
        "--K1", K1,
        "--K2", K2,
        "--N","6",
        "--ref","step"
    ], capsys)
    assert "summary" in sres and sres["summary"]["N"] == 6
