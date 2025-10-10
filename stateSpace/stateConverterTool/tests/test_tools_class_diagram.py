from __future__ import annotations
import subprocess, sys, pathlib

TOOLS = pathlib.Path(__file__).resolve().parents[1] / "tools"

def test_class_diagram_tool_creates_puml(tmp_path):
    # run the tool in its package dir to write puml in cwd
    res = subprocess.run([sys.executable, "class_diagram.py"], cwd=str(TOOLS), capture_output=True, text=True)
    assert res.returncode == 0
    assert "Wrote ./stateConverterTool_class_diagram.puml" in res.stdout
