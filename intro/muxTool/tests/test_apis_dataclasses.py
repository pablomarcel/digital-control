
from intro.muxTool.apis import RunRequest, RunResult

def test_runrequest_defaults_and_fields():
    r = RunRequest()
    assert r.csv is None and r.json is None and r.out is None
    assert r.bits == 8 and r.in_dir == "in" and r.out_dir == "out"

def test_runresult_container():
    rr = RunResult(rows=[{"cycle":0,"sel":0,"d0":1,"d1":2,"d2":3,"d3":4,"y":1}], out_csv="x.csv", out_vcd="x.vcd")
    assert rr.rows and rr.rows[0]["y"] == 1
    assert rr.out_csv.endswith(".csv") and rr.out_vcd.endswith(".vcd")
