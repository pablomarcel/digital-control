
from __future__ import annotations
import os, json, logging, pprint
import numpy as np

from polePlacement.controllabilityTool.app import ControllabilityApp
from polePlacement.controllabilityTool.apis import RunRequest

pp = pprint.PrettyPrinter(indent=2)

def test_app_json_ct_gramian_and_report(tmp_path, capsys):
    # Turn logging to DEBUG (most verbose)
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(name)s: %(message)s")

    # Write a local JSON system file
    sys_json = tmp_path / "ct_demo.json"
    payload = {
        "A": [[0.0, 1.0], [-2.0, -3.0]],
        "B": [[0.0],[1.0]],
        "discrete": False
    }
    json.dump(payload, open(sys_json, "w"))
    report_path = tmp_path / "rep.txt"

    print("[TEST] sys_json:", sys_json)
    print("[TEST] json payload:"); print(json.dumps(payload, indent=2))
    print("[TEST] report_path:", report_path)

    app = ControllabilityApp()
    req = RunRequest(json_path=str(sys_json), name="ct_demo_run",
                     pbh=True, gram=True, pretty=True, save_json=True, save_gram=True,
                     report=str(report_path), log="DEBUG")
    print("[TEST] RunRequest:"); print(req)

    res = app.run(req)
    print("[TEST] RunResult.exit_code:", res.exit_code)
    print("[TEST] RunResult.summary_json:"); print(res.summary_json)

    # capture and show any stdout/stderr from pretty printing
    captured = capsys.readouterr()
    print("[TEST] captured stdout START >>>")
    print(captured.out)
    print("[TEST] captured stdout END <<<")

    # We don't assert on report file presence (not part of app), just sanity checks
    assert res.exit_code in (0,2)
    assert isinstance(res.summary_json, str) and '"name": "ct_demo_run"' in res.summary_json

def test_app_dt_inf_gramian_and_finite():
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(name)s: %(message)s")
    app = ControllabilityApp()
    A="0.98 0; 0 0.95"
    B="0.1; 1"
    req = RunRequest(A=A,B=B,discrete=True,gram=True,finite_dt=10,name="dt_inf_fin",save_gram=True, pretty=True, log="DEBUG")
    res = app.run(req)
    assert res.exit_code in (0,2)

def test_app_symbolic_rank_and_output_ctrb(tmp_path):
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(name)s: %(message)s")
    app = ControllabilityApp()
    req = RunRequest(A="0 1; -2 -3", B="0; 1", C="1 0",
                     symbolic=True, output_ctrb=True, save_output_csv=True, name="sym_out", pretty=True, log="DEBUG")
    res = app.run(req)
    assert res.exit_code in (0,2)
