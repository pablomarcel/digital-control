# -*- coding: utf-8 -*-
from systemDesign.frequencyResponseTool.tools.class_diagram import main

def test_class_diagram(tmp_path):
    p = main(str(tmp_path))
    assert p.endswith(".puml")
    assert (tmp_path / "frequencyResponseTool_class_diagram.puml").exists()
