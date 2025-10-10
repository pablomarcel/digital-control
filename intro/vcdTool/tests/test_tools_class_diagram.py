import os
from intro.vcdTool.tools.class_diagram import main

def test_class_diagram_writes(tmp_path):
    main(str(tmp_path))
    p = tmp_path / "vcdTool_class_diagram.puml"
    assert p.exists()
