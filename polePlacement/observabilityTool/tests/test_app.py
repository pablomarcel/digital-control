
from polePlacement.observabilityTool.app import ObservabilityApp
from polePlacement.observabilityTool.apis import RunRequest

def test_app_basic_discrete_observable(tmp_path):
    app = ObservabilityApp()
    req = RunRequest(A="-1 0; 0 -2", C="1 5", discrete=True, pretty=False, name="t_app")
    res = app.run(req)
    assert res.exit_code == 0
    assert '"full_obsv_rank_n": true' in res.summary_json
