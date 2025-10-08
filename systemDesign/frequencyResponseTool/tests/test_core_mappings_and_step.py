# -*- coding: utf-8 -*-
import os, numpy as np
from systemDesign.frequencyResponseTool.core import (
    Lead, Lag, LagLead, lead_w_to_z, lag_w_to_z, laglead_w_to_z,
    z_to_w, step_response_csv
)

def test_lead_lag_to_z_forms():
    T = 0.2
    L = Lead(1.0, 0.4, 0.5)
    n,d = lead_w_to_z(L, T)
    assert len(n) == len(d) == 2

    G = Lag(1.5, 4.0, 0.3)
    n2,d2 = lag_w_to_z(G, T)
    assert len(n2) == len(d2) == 2

    LL = LagLead(1.0, 4.0, 0.8, 0.4, 0.2)
    n3,d3 = laglead_w_to_z(LL, T)
    assert len(n3) == len(d3)

def test_z_to_w_simple():
    # Identity plant maps to identity
    num_w, den_w = z_to_w([1.0], [1.0], T=0.1)
    assert np.allclose(num_w, [1.0]) and np.allclose(den_w, [1.0])

def test_step_response_csv(tmp_path):
    csv = tmp_path / "step.csv"
    # Use trivial closed-loop C(z)/R(z) ~ 1 (num=den)
    step_response_csv([1.0], [1.0], T=0.1, N=10, out_csv=str(csv))
    assert csv.exists()
    head = csv.read_text().splitlines()[0]
    assert "k,t,c(k)" in head
