from __future__ import annotations
import json, subprocess, sys, os, shlex
from introduction.demuxTool.apis import RunRequest
from introduction.demuxTool.app import DemuxApp

def test_app_run_inline_json(tmp_path):
    req = RunRequest(json_spec='[{"sel":0,"x":1},{"sel":1,"x":2}]',
                     n_outputs=4, data_bw=4, out_csv=str(tmp_path/'out.csv'))
    res = DemuxApp().run(req)
    assert len(res.rows) == 2
    assert os.path.exists(req.out_csv)

def test_cli_help_runs():
    # Execute cli.py with --help from inside the package
    pkg_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    cli = os.path.join(pkg_dir, "cli.py")
    assert os.path.exists(cli)
    cp = subprocess.run([sys.executable, cli, "--help"], capture_output=True, text=True)
    assert cp.returncode == 0
    assert "demultiplexer" in cp.stdout.lower()
