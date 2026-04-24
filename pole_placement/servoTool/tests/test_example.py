from __future__ import annotations
import numpy as np

from pole_placement.servoTool.app import ServoApp
from pole_placement.servoTool.apis import RunRequest

def test_design_example():
    app = ServoApp()
    req = RunRequest(
        mode='design',
        G='0 1 0; 0 0 1; -0.12 -0.01 1',
        H='0;0;1',
        C='0.5 1 0',
        which='ogata',
        method='acker',
    )
    res = app.run(req)
    assert isinstance(res.meta, dict)
    assert len(res.K1) == 1

def test_observer_example():
    app = ServoApp()
    req = RunRequest(
        mode='observer',
        G='0 1 0; 0 0 1; -0.12 -0.01 1',
        H='0;0;1',
        C='0.5 1 0',
        method='acker',
        poles='0,0'
    )
    res = app.run(req)
    assert isinstance(res.notes, str)
    assert len(res.Ke) > 0

def test_sim_example():
    app = ServoApp()
    dreq = RunRequest(
        mode='design',
        G='0 1 0; 0 0 1; -0.12 -0.01 1',
        H='0;0;1',
        C='0.5 1 0',
        which='ogata',
        method='acker',
    )
    dres = app.run(dreq)
    K1 = ' '.join(str(v) for v in np.array(dres.K1).ravel().tolist())
    K2 = ' '.join(str(v) for v in np.array(dres.K2).ravel().tolist())

    sreq = RunRequest(
        mode='sim',
        G='0 1 0; 0 0 1; -0.12 -0.01 1',
        H='0;0;1',
        C='0.5 1 0',
        K1=K1,
        K2=K2,
        N=10,
        ref='step',
    )
    sres = app.run(sreq)
    assert len(sres.y) == 10
