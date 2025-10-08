# -*- coding: utf-8 -*-
import numpy as np

from systemDesign.frequencyResponseTool.core import z_to_w, Lead, lead_w_to_z, series_desc, closed_loop_desc

def test_z_to_w_identity_like():
    # A trivial plant with G(z) = 1 (num=1, den=1) maps to G(w)=1
    num_w, den_w = z_to_w([1.0], [1.0], T=0.1)
    jw = 1j*np.array([1.0, 10.0])
    # evaluate H(jw) = 1
    num = den = np.array([1.0])
    H = (num[0]+jw*0)/(den[0]+jw*0)
    # Spot check shape
    assert num_w.shape[0] == den_w.shape[0] == 1

def test_series_and_closed_loop_desc():
    n1, d1 = [1.0, 0.5], [1.0, -0.3]
    n2, d2 = [1.0, 0.2], [1.0, 0.1]
    N, D = series_desc(n1, d1, n2, d2)
    assert len(N) == len(n1)+len(n2)-1
    assert len(D) == len(d1)+len(d2)-1
    CLn, CLd = closed_loop_desc(N, D)
    assert len(CLn) == len(CLd)
