
from __future__ import annotations
import numpy as np

from pole_placement.observerTool.design import design_observer, closedloop_poles, simulate


def test_prediction_observer_and_separation():
    A = "1 0.2; 0 1"
    B = "0.02; 0.2"
    C = "1 0"
    K = "8 3.2"
    L = design_observer("prediction", A, C, poles="0,0", method="acker")["L"]
    res = closedloop_poles(A, B, C, K, L.tolist())
    assert res["separation_ok"] is True


def test_simulate_step_basic():
    A = "1 0.2; 0 1"
    B = "0.02; 0.2"
    C = "1 0"
    K = "8 3.2"
    # simple stable L
    L = "2; 5"
    payload = simulate(A, B, C, K, L, N=10, Ts=0.2, ref="step", K0="auto")
    assert "y" in payload and "u" in payload
    assert len(payload["y"]) == 10
