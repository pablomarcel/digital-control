from __future__ import annotations
import json, pytest
from intro.zohTool.app import ZOHApp
from intro.zohTool.apis import RunRequest

def test_app_json_no_outputs(tmp_path):
    # no CSV/VCD requested -> wrote_* remain None
    req = RunRequest(json_spec='[1,2,3]', Ts=0.1, out_dir=str(tmp_path))
    res = ZOHApp().run(req)
    assert len(res.events) == 3
    assert res.wrote_csv is None and res.wrote_vcd is None

def test_app_errors_without_source():
    with pytest.raises(ValueError):
        ZOHApp().run(RunRequest())
