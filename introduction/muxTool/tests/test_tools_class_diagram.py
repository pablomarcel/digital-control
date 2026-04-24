
import sys, subprocess, pathlib

def test_class_diagram_tool(tmp_path):
    pkg_dir = pathlib.Path(__file__).resolve().parents[1]
    out = tmp_path / "muxTool_class.mmd"
    res = subprocess.run([sys.executable, "tools/class_diagram.py", "--out", str(out)], cwd=str(pkg_dir), text=True, capture_output=True, check=True)
    assert out.exists()
    txt = out.read_text()
    assert "classDiagram" in txt and "MuxApp --> MuxCore" in txt
