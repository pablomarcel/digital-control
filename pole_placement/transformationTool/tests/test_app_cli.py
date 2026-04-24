
from __future__ import annotations
import os, json, tempfile
import numpy as np

from pole_placement.transformationTool.apis import RunRequest
from pole_placement.transformationTool.app import TransformationApp
from pole_placement.transformationTool.cli import main as cli_main

def test_app_multiple_transforms(tmp_path, monkeypatch):
    # ensure outputs go to real out/ under package (already default); just run
    A = np.array([[0,1],[-2,-3]], dtype=complex)
    B = np.array([[0],[1]], dtype=complex)
    C = np.array([[1,0]], dtype=complex)
    req = RunRequest(A=A,B=B,C=C,to_ccf=True,to_diag=True,show_tf=True,pretty=True,save_json=True,save_csv=True,name="cov")
    res = TransformationApp().run(req)
    assert len(res) == 2
    # CSV/JSON likely created for both
    outdir = os.path.join(os.path.dirname(__file__), "..", "out")
    # don't assert filesystem here—just smoke that run did not raise

def test_cli_with_json_and_args(tmp_path):
    # create input JSON
    j = tmp_path / "sys.json"
    j.write_text(json.dumps({"A": [[0,1],[-2,-3]], "B": [[0],[1]], "C": [[1,0]], "D": [[0]]}))
    # run cli: CCF + OCF
    rc = cli_main(["--json", str(j), "--to-ccf", "--to-ocf", "--name", "cli_json"])
    assert rc == 0 or rc is None

def test_cli_with_matrices():
    rc = cli_main(["--A","0 1; -2 -3","--B","0;1","--C","1 0","--to-diag","--name","cli_diag"])
    assert rc == 0 or rc is None
