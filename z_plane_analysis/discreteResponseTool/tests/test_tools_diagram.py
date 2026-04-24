
from z_plane_analysis.discreteResponseTool.tools.class_diagram import main
def test_class_diagram(tmp_path):
    main(str(tmp_path))
    assert (tmp_path / "discreteResponseTool_class_diagram.puml").exists()
