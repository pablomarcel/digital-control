
from systemDesign.juryTestTool.tools.class_diagram import main
from systemDesign.juryTestTool.utils import out_path

def test_class_diagram_writes():
    main()
    assert out_path("juryTestTool_class_diagram.puml").exists()
