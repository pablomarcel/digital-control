
import pytest
from z_plane_analysis.discreteResponseTool.core import sig
from z_plane_analysis.discreteResponseTool.apis import RunRequest
from z_plane_analysis.discreteResponseTool.app import DiscreteResponseApp

@pytest.mark.skipif(sig is None, reason="scipy not installed in test environment")
def test_app_example37_smoke(tmp_path):
    req = RunRequest(example37=True, N=5, matplotlib=str(tmp_path / "resp.png"), outdir=str(tmp_path))
    app = DiscreteResponseApp(req)
    out = app.run(matplotlib=req.matplotlib, outdir=req.outdir)
    assert "matplotlib" in out
