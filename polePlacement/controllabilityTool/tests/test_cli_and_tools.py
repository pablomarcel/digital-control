
from __future__ import annotations
import os, sys

from polePlacement.controllabilityTool import cli
from polePlacement.controllabilityTool.tools import class_diagram

BASE = os.path.dirname(os.path.dirname(__file__))

def run_cli(args):
    old = sys.argv[:]
    try:
        sys.argv = ["cli.py"] + args
        return cli.main()
    finally:
        sys.argv = old

def test_cli_end_to_end():
    code = run_cli(["--A","0 1; -2 -3","--B","0; 1","--name","cli_run","--save-json"])
    assert code in (0,2)
    assert os.path.exists(os.path.join(BASE,"out","cli_run_summary.json"))

def test_class_diagram_tool():
    class_diagram.main()
    p = os.path.join(BASE,"out","controllabilityTool_class_diagram.puml")
    assert os.path.exists(p)
