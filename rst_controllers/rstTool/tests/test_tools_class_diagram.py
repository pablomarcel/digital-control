
import os
from rst_controllers.rstTool.tools.class_diagram import main as diagram_main

def test_class_diagram_writer():
    diagram_main()
    assert os.path.exists(os.path.join("rst_controllers","rstTool","out","rstTool_class_diagram.puml"))
