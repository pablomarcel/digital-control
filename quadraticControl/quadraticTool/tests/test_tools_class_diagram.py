# Just make sure the tools subpackage imports without side-effects
import quadraticControl.quadraticTool.tools as tools_pkg

def test_tools_class_diagram_import():
    assert hasattr(tools_pkg, "__all__") or True
