
import sympy as sp
from stateSpace.stateSolverTool.app import StateSolverApp
from stateSpace.stateSolverTool.apis import RunRequest

def test_app_example_ogata_5_2_brief_ok():
    app = StateSolverApp(pkg_dir = __import__("os").path.dirname(__file__))
    res = app.run(RunRequest(example="ogata_5_2", latex=False, check="brief", steps=4))
    assert res.mode == "lti"
    assert res.lti.check_status == "ok."
    assert res.lti.Psi.shape == (2,2)
    assert res.lti.xk.shape == (2,1)
    assert res.lti.yk.shape == (1,1)
