from __future__ import annotations
import os, json
from introduction.zohTool.app import ZOHApp
from introduction.zohTool.apis import RunRequest

def test_app_runs_with_json_and_writes(tmp_path):
    outdir = tmp_path / 'out'
    req = RunRequest(
        json_spec='[0, 0.5, 1.0]',
        Ts=0.1,
        out_dir=str(outdir),
        out_csv='res.csv',
        out_vcd='res.vcd',
        units='V',
        scale=1e3
    )
    res = ZOHApp().run(req)
    assert len(res.events) == 3
    assert (outdir / 'res.csv').exists()
    assert (outdir / 'res.vcd').exists()
