
from __future__ import annotations
import numpy as np
from pole_placement.observerTool.core import (
    design_prediction_observer, design_current_observer, dlqe_gain,
    design_minimum_order_observer, minobs_step, reconstruct_xhat_from_minobs,
    k0_state, k0_ogata, ke_rule_of_thumb, ke_grid_search,
    simulate_full_observer
)

def _plant():
    T = 0.2
    A = np.array([[1.0, T],[0.0, 1.0]])
    B = np.array([[T*T/2],[T]])
    C = np.array([[1.0, 0.0]])
    return A,B,C

def test_designers_and_minobs_and_k0():
    A,B,C = _plant()
    Lp = design_prediction_observer(A, C, [0,0], method="acker")
    Lc = design_current_observer(A, C, [0,0], method="acker")
    assert Lp.shape == (2,1) and Lc.shape == (2,1)
    # dlqe
    G = np.eye(2)
    Qn = np.eye(2)
    Rn = np.array([[1.0]])
    L, P, E = dlqe_gain(A, G, C, Qn, Rn)
    assert L.shape == (2,1) and P.shape == (2,2)
    # min-order
    d = design_minimum_order_observer(A, B, C, [0], method="acker")
    assert d.Ke.shape == (1,1)
    # minobs step and reconstruct
    eta, xbh = minobs_step(d.Ke, d.blocks, np.array([[0.0]]), np.array([[0.0]]), np.array([[0.0]]))
    xhat = reconstruct_xhat_from_minobs(d.T, np.array([[0.0]]), xbh)
    assert xhat.shape == (2,1)
    # k0 state & ogata
    K = np.array([[8.0, 3.2]])
    k0s = k0_state(A,B,C,K)
    k0o = k0_ogata(A,B,C,K,Lp,extra_gain=1.0)
    assert k0s > 0 and k0o > 0

def test_selection_and_sim():
    A,B,C = _plant()
    K = np.array([[8.0,3.2]])
    Lrt, poles = ke_rule_of_thumb(A, C, [0.9, 0.8], speedup=2.0)
    assert Lrt.shape[0] == 2
    score, sp, L = ke_grid_search(A, C, B, K, [[0.2,0.2],[0.5,0.5]], steps=5)
    assert L is not None and score >= 0.0
    res = simulate_full_observer(A, B, C, K, Lrt, N=5, Ts=0.2, K0=1.0)
    assert "y" in res and len(res["y"]) == 5
