from __future__ import annotations
import numpy as np
import pytest
from polePlacement.servoTool.app import ServoApp
from polePlacement.servoTool.apis import RunRequest

def test_app_aug_design_branch():
    app = ServoApp()
    res = app.run(RunRequest(
        mode='design',
        G='0 1 0; 0 0 1; -0.12 -0.01 1',
        H='0;0;1',
        C='0.5 1 0',
        which='aug'
    ))
    assert res.meta['which'] == 'aug'

def test_app_missing_G_raises():
    app = ServoApp()
    with pytest.raises(ValueError):
        app.run(RunRequest(mode='design', H='0;1', C='1 0'))

def test_app_sim_missing_K_raises():
    app = ServoApp()
    with pytest.raises(ValueError):
        app.run(RunRequest(mode='sim', G='1', H='1', C='1'))

def test_app_sim_use_observer_needs_ke_t():
    app = ServoApp()
    # first get K
    d = app.run(RunRequest(mode='design', G='1', H='1', C='1'))
    K1 = str(d.K1[0][0]); K2 = str(d.K2[0][0])
    with pytest.raises(ValueError):
        app.run(RunRequest(mode='sim', G='1', H='1', C='1',
                           K1=K1, K2=K2, use_observer=True))
