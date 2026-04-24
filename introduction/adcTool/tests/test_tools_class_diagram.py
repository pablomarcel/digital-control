
import os
from introduction.adcTool.tools.class_diagram import main as classdiag_main

def test_class_diagram_tool(tmp_path):
    out = tmp_path / "uml"
    classdiag_main(str(out))
    p = out / "adcTool_class_diagram.puml"
    assert p.exists()
    txt = p.read_text()
    assert "@startuml" in txt and "ADCApp" in txt and "CounterADC" in txt
