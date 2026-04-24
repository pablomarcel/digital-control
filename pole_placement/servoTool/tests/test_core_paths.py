from __future__ import annotations
import numpy as np
import pytest
from pole_placement.servoTool.core import (acker, design_servo_ogata, design_servo_aug,
                                           design_min_observer, simulate_servo, MinObserver, place_wrapper)

def test_acker_uncontrollable_raises():
    A = np.array([[1,0],[0,1]])
    B = np.array([[1],[0]])  # second state uncontrollable
    with pytest.raises(ValueError):
        acker(A,B,[0,0])

def test_place_wrapper_unknown_falls_back():
    A = np.array([[0,1],[0,0]])
    B = np.array([[0],[1]])
    # For state feedback, K is 1 x n (n states), regardless of #inputs (SISO here)
    K = place_wrapper(A,B,[0,0],"does_not_exist")
    assert K.shape == (1, A.shape[0])

def test_servo_design_ogata_and_aug():
    G = np.array([[0,1,0],[0,0,1],[-0.12,-0.01,1.0]])
    H = np.array([[0.0],[0.0],[1.0]])
    C = np.array([[0.5,1.0,0.0]])
    K1o, K2o = design_servo_ogata(G,H,C)
    K1a, K2a = design_servo_aug(G,H,C)
    assert K1o.shape[1] == 1 and K2o.shape[1] == 3
    assert K1a.shape[1] == 1 and K2a.shape[1] == 3

def test_min_observer_and_sim_prediction():
    G = np.array([[0,1,0],[0,0,1],[-0.12,-0.01,1.0]])
    H = np.array([[0.0],[0.0],[1.0]])
    C = np.array([[0.5,1.0,0.0]])
    K1, K2 = design_servo_ogata(G,H,C)
    mob = design_min_observer(G,H,C,poles=[0,0])
    sim = simulate_servo(G,H,C,K1,K2,N=8,r_type="ramp",use_observer=True,minobs=mob,observer_mode="prediction")
    assert len(sim.y) == 8

def test_sim_errors():
    G = np.eye(2); H = np.ones((2,1)); C = np.array([[1,0]])
    K1 = np.array([[1.0]]); K2 = np.array([[0.1,0.2]])
    from pole_placement.servoTool.core import simulate_servo
    with pytest.raises(ValueError):
        simulate_servo(G,H,C,K1,K2,N=2,use_observer=True,minobs=None)
