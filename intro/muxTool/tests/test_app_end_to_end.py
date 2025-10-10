
import json, pathlib
from intro.muxTool.app import MuxApp
from intro.muxTool.apis import RunRequest

def test_app_runs_with_csv(tmp_path):
    csvp = tmp_path / "in.csv"
    csvp.write_text("sel,d0,d1,d2,d3\n0,1,2,3,4\n1,5,6,7,8\n")
    req = RunRequest(csv=str(csvp), out="o.csv", bits=8, trace="o.vcd", in_dir=str(tmp_path), out_dir=str(tmp_path))
    res = MuxApp().run(req)
    assert (tmp_path / "o.csv").exists()
    assert (tmp_path / "o.vcd").exists()
    assert [r["y"] for r in res.rows] == [1,6]

def test_app_runs_with_inline_json(tmp_path):
    json_inline = json.dumps([{"sel":0,"d0":1,"d1":2,"d2":3,"d3":4}])
    req = RunRequest(json=json_inline, out="o.csv", bits=4, trace=None, in_dir=str(tmp_path), out_dir=str(tmp_path))
    res = MuxApp().run(req)
    assert (tmp_path / "o.csv").exists()
    assert res.rows[0]["y"] == 1
