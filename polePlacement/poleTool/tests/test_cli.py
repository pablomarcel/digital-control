from __future__ import annotations
import os, sys, json
from pathlib import Path

def run_cli(argv):
    # Import inside to exercise import shim path in user repo, but here we call main() directly.
    from polePlacement.poleTool import cli
    return cli.main(argv)

def test_cli_ackermann_mpl(tmp_path, capsys):
    outdir = tmp_path / "out"
    argv = [
        "--A","0 1; -0.16 -1",
        "--B","0; 1",
        "--C","1 0",
        "--poles","0.5+0.5j,0.5-0.5j",
        "--plot","mpl",
        "--style","dots",
        "--save_json",
        "--save_csv",
        "--name","cli_ack",
        "--outdir", str(outdir),
    ]
    run_cli(argv)
    # artifacts
    assert (outdir / "cli_ack_step_mpl.png").exists()
    assert (outdir / "cli_ack_step.csv").exists()
    assert (outdir / "cli_ack.json").exists()
    # stdout sanity
    out = capsys.readouterr().out
    assert "RESULTS" in out

def test_cli_json_in(tmp_path):
    # Prepare json file with A,B,C
    sys_json = tmp_path / "sys_tf.json"
    data = {"A": [[0,1],[-0.16,-1]], "B": [[0],[1]], "C": [[1,0]]}
    sys_json.write_text(json.dumps(data), encoding="utf-8")
    outdir = tmp_path / "o2"
    from polePlacement.poleTool import cli
    argv = [
        "--json_in", str(sys_json),
        "--poles","0.4+0.3j,0.4-0.3j",
        "--plot","none",
        "--save_json",
        "--name","from_json",
        "--outdir", str(outdir),
    ]
    cli.main(argv)
    assert (outdir / "from_json.json").exists()
