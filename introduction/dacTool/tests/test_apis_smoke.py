
from __future__ import annotations
from introduction.dacTool.apis import RunRequest, RunResult, Row, Update

def test_apis_construct():
    rr = RunRequest(dac_type="weighted", nbits=4, vref=2.5, jspec="[0,1,2]")
    u = Update(code=3, vo_ideal=1.0, vo_nonideal=1.1)
    r = Row(meta={"a":1})
    res = RunResult(rows=[r], updates=[u], messages=["ok"])
    assert rr.dac_type == "weighted"
    assert res.updates[0].code == 3
