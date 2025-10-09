
import pathlib
from polePlacement.observabilityTool.tools.class_diagram import main as class_diag_main
from polePlacement.observabilityTool.utils import pkg_outdir

def test_class_diagram_writes_file():
    class_diag_main("out")
    p = pathlib.Path(pkg_outdir())/"observabilityTool_class_diagram.puml"
    assert p.exists()
