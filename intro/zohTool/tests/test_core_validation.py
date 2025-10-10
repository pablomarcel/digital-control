from __future__ import annotations
import math, pytest
from intro.zohTool.core import ZOHModel

def test_model_validations():
    with pytest.raises(ValueError):
        ZOHModel(Ts=0.0)
    with pytest.raises(ValueError):
        ZOHModel(Ts=0.1, delay=-1.0)
    # droop_tau NaN is invalid
    with pytest.raises(ValueError):
        ZOHModel(Ts=0.1, droop_tau=float('nan'))

def test_model_ok_infinite_tau():
    m = ZOHModel(Ts=0.1, droop_tau=math.inf)
    assert m.droop_tau == math.inf
