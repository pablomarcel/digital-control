
from __future__ import annotations
import numpy as np
from rst_controllers.rstPlotTool.core import step_metrics, robust_limits

def test_step_metrics_simple():
    k = np.arange(0, 5)
    r = np.ones_like(k, dtype=float)
    y = np.array([0.0, 0.4, 0.8, 1.02, 1.0])
    m = step_metrics(k, r, y)
    assert 0 <= m['overshoot'] <= 5
    assert m['yf'] == 1.0
    assert m['tsettle'] >= 0

def test_robust_limits_edges():
    import numpy as np
    lo, hi = robust_limits(np.array([]), 0.9)
    assert lo < hi
    lo2, hi2 = robust_limits(np.array([5,5,5], float), 0.9)
    assert lo2 < hi2  # expanded symmetric range
