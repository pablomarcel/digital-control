
import os, time
from state_space.stateSolverTool.utils import out_path, timeit
from state_space.stateSolverTool.tools import class_diagram as cd

def test_out_path_creates_out_dir(tmp_path):
    pkg_dir = os.path.dirname(cd.__file__)  # inside tools/, go up to package via function
    pkg_dir = os.path.dirname(pkg_dir)
    p = out_path(pkg_dir, "touch.txt")
    with open(p, "w") as f: f.write("ok")
    assert os.path.exists(p)

def test_timeit_decorator_runs_and_returns_value():
    @timeit
    def f(x): return x + 1
    assert f(2) == 3

def test_class_diagram_writer():
    # Should write into package 'out/' by default
    cd.main()
    pkg_dir = os.path.dirname(os.path.dirname(cd.__file__))
    p = os.path.join(pkg_dir, "out", "stateSolverTool_class_diagram.puml")
    assert os.path.exists(p)
