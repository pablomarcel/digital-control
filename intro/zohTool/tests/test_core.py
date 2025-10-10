from __future__ import annotations
import math
from intro.zohTool.core import ZOHModel, ZOHSimulator

def test_expand_constant_ideal():
    model = ZOHModel(Ts=0.1, delay=0.0, droop_tau=math.inf, offset=0.0)
    sim = ZOHSimulator(model)
    evs = sim.expand([0.0, 1.0, 2.0])
    assert len(evs) == 3
    assert evs[0].t0 == 0.0 and evs[0].t1 == 0.1 and evs[0].y0 == 0.0 and evs[0].y1 == 0.0
    assert evs[1].t0 == 0.1 and evs[1].t1 == 0.2 and evs[1].y0 == 1.0 and evs[1].y1 == 1.0

def test_expand_with_droop():
    model = ZOHModel(Ts=1.0, delay=0.0, droop_tau=2.0, offset=0.0)
    sim = ZOHSimulator(model)
    evs = sim.expand([1.0])
    assert len(evs) == 1
    assert evs[0].y0 == 1.0
    assert 0.6 < evs[0].y1 < 0.7  # exp(-1/2) ~ 0.6065
