
import os, sys, shlex
from rstControllers.rstTool import cli

def test_cli_main_pretty(capsys, monkeypatch):
    args = "--A '1 -0.8' --B '0.5' --d 1 --poles '0.6 0.6' --Tmode unity_dc --pretty --step 40 --save_csv --export_json"
    monkeypatch.setattr(sys, "argv", ["prog"] + shlex.split(args))
    cli.main()
    out = capsys.readouterr().out
    assert "Controller (RST)" in out
    # outputs should have been written to out/
    assert os.path.exists(os.path.join("rstControllers","rstTool","out","rst.csv"))
    assert os.path.exists(os.path.join("rstControllers","rstTool","out","rst_design.json"))
