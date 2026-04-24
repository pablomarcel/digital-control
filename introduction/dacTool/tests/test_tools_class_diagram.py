
from __future__ import annotations
import os, pathlib
from introduction.dacTool.tools.class_diagram import main as class_diagram_main

def test_class_diagram_writes(tmp_path):
    class_diagram_main(str(tmp_path))
    p = tmp_path / "dacTool_class_diagram.puml"
    assert p.exists()
    assert "@startuml" in p.read_text()
