from __future__ import annotations
from intro.zohTool.tools.class_diagram import main

def test_class_diagram_tool(tmp_path):
    path = main(str(tmp_path))
    assert (tmp_path / "zohTool_class_diagram.puml").exists()
