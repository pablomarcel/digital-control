
import json, pathlib, numpy as np
from kalman_filters.kalmanFilterTool.apis import RunRequest
from kalman_filters.kalmanFilterTool.app import KalmanFilterApp

def test_app_build_and_run_csv_and_meta(tmp_path):
    out_dir = tmp_path / "out"
    req = RunRequest(dt=0.05, T=0.2, q=0.1, r=1.5, backend="none",
                     save_csv="kf.csv", out_dir=str(out_dir))
    result = KalmanFilterApp().build_and_run(req)
    meta = pathlib.Path(result["meta_path"])
    assert meta.exists()
    csv = out_dir / "kf.csv"
    assert csv.exists()
    data = json.loads(meta.read_text())
    assert "A" in data and "R" in data and data["dt"] == 0.05
