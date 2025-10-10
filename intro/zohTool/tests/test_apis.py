from __future__ import annotations
from intro.zohTool.apis import IntervalEvent

def test_intervalevent_as_dict():
    d = IntervalEvent(1, 0.0, 0.1, 2.0, 3.0, 4.0).as_dict()
    assert d["k"] == 1 and d["u_in"] == 2.0 and "t1" in d
