
import sys
from z_plane_analysis.discreteResponseTool import cli

def test_cli_main_runs(monkeypatch, tmp_path):
    argv = ["prog","--example37","--N","5","--outdir",str(tmp_path)]
    monkeypatch.setattr(sys, "argv", argv)
    cli.main()  # should not raise
