
import os, sys, json
from stateSpace.stateSpaceTool import cli

def run_cli(args):
    old = sys.argv[:]
    try:
        sys.argv = ["cli.py"] + args
        cli.main()
    finally:
        sys.argv = old

def test_cli_example_and_exports(tmp_path):
    out_json = tmp_path / "ex.json"
    out_tex = tmp_path / "ex.tex"
    run_cli(["--example","ogata_5_1","--json-out", str(out_json), "--latex-out", str(out_tex), "--check","brief"])
    assert out_json.exists() and out_tex.exists()
    data = json.loads(out_json.read_text())
    assert "cont" in data

def test_cli_zmin1_and_diag():
    run_cli(["--form","zmin1","--den","1 1.3 0.4","--num","0 1 1","--forms","diag","--check","off"])
