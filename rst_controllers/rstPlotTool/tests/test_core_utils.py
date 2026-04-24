from __future__ import annotations
import numpy as np
from rst_controllers.rstPlotTool.core import robust_limits, crop_by_k

def test_robust_limits_monotone():
    x = np.linspace(-10, 10, 1000)
    lo, hi = robust_limits(x, 0.98)
    assert lo < 0 and hi > 0
    lo2, hi2 = robust_limits(x, 1.0)
    assert lo2 <= lo and hi2 >= hi

def test_crop_by_k_basic():
    d = dict(k=np.array([0,1,2,3,4], float),
             r=np.ones(5), y=np.ones(5), u=np.zeros(5), v=np.zeros(5), e=np.zeros(5))
    out = crop_by_k(d, 1, 3)
    assert out["k"][0] == 1 and out["k"][-1] == 3
