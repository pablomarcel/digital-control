
import os
from z_plane_analysis.discreteResponseTool.utils import with_outdir_policy

@with_outdir_policy
def _fake_export(*, matplotlib=None, csv=None, pzmap=None, outdir="out"):
    return {"matplotlib": matplotlib, "csv": csv, "pzmap": pzmap}

def test_with_outdir_policy(tmp_path):
    out = _fake_export(matplotlib="a.png", csv=str(tmp_path / "c.csv"), pzmap="b.png", outdir=str(tmp_path))
    # Relative paths should be normalized under outdir, absolute path preserved
    assert out["matplotlib"].startswith(str(tmp_path))
    assert out["csv"] == str(tmp_path / "c.csv")
    assert out["pzmap"].startswith(str(tmp_path))
