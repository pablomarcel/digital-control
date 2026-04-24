from __future__ import annotations
from pole_placement.poleTool.app import PolePlacementApp
from pole_placement.poleTool.apis import RunRequest

def test_app_basic_run(tmp_path, monkeypatch):
    # Force outputs into tmp_path
    req = RunRequest(
        A="0 1; -0.16 -1",
        B="0; 1",
        C="1 0",
        poles="0.5+0.5j,0.5-0.5j",
        method="ackermann",
        plot="none",
        save_json=True,
        save_csv=True,
        name="tcase",
        outdir=str(tmp_path)
    )
    app = PolePlacementApp()
    res = app.run(req)
    assert res["placement_error"] < 1e-8
    assert (tmp_path / "tcase.json").exists()
    assert (tmp_path / "tcase_step.csv").exists()
