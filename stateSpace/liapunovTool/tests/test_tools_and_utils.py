import os
from stateSpace.liapunovTool.tools import class_diagram as cd
from stateSpace.liapunovTool.utils import timed

def test_class_diagram_write(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cd.main()
    assert os.path.exists(tmp_path / "out" / "liapunovTool_class_diagram.puml")

def test_timed_decorator():
    @timed
    def f(x): 
        return x * 2
    r = f(3)
    assert r == 6
