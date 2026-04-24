
from __future__ import annotations
import os
from rst_controllers.rstPlotTool.tools.class_diagram import main

def test_class_diagram_generator(tmp_path):
    main(str(tmp_path))
    assert (tmp_path / "rstPlotTool_class_diagram.puml").exists()
