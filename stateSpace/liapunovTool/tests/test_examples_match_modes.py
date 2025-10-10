import sympy as sp
from stateSpace.liapunovTool.apis import RunRequest
from stateSpace.liapunovTool.app import LyapunovApp

def test_example_ogata_5_8():
    app = LyapunovApp()
    res = app.run(RunRequest(mode="example", which="ogata_5_8", digits=10))
    assert res.mode == "ct"
    # P must be symmetric positive definite
    assert res.P == res.P.T
    assert res.pd_class in ("positive definite", "unknown")

def test_example_ogata_5_9():
    app = LyapunovApp()
    res = app.run(RunRequest(mode="example", which="ogata_5_9", digits=10))
    assert res.mode == "dt"
    assert res.P == res.P.T
    assert res.pd_class in ("positive definite", "unknown")
