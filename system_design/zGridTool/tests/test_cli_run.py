
# -*- coding: utf-8 -*-
from __future__ import annotations
import os, sys, pathlib, subprocess, json

def test_cli_mpl_run(tmp_path, monkeypatch):
    """
    End-to-end CLI run on MPL backend, executed from inside the package dir
    so the import shim is exercised. Also tests:
      - --fs instead of --T
      - --export_csv_prefix (CSV outputs)
      - P/Z overlay loading from in/ with JSON
    """
    # Locate package dir
    pkg_dir = pathlib.Path(__file__).resolve().parents[1]
    cli = pkg_dir / "cli.py"
    assert cli.exists()

    # Create an overlay JSON under package in/
    in_dir = pkg_dir / "in"
    in_dir.mkdir(exist_ok=True, parents=True)
    overlay = {
        "poles": ["0.8+0.2j", {"re": 0.6, "im": -0.3, "label": "p1"}],
        "zeros": [[0.5, 0.0]]
    }
    ov_path = in_dir / "overlay.json"
    ov_path.write_text(json.dumps(overlay))

    # Run
    env = os.environ.copy()
    # Favor the project root import; project root = system_design/..
    project_root = pkg_dir.parent.parent
    env["PYTHONPATH"] = os.pathsep.join([str(project_root), env.get("PYTHONPATH","")])

    out_png = "cli_run.png"
    csv_prefix = "cli_curves"

    cmd = [sys.executable, str(cli),
           "--fs", "20",                # T = 0.05
           "--backend", "mpl",
           "--export_csv_prefix", csv_prefix,
           "--png", out_png,
           "--pz", "overlay.json"]
    res = subprocess.run(cmd, cwd=str(pkg_dir), env=env, capture_output=True, text=True)
    assert res.returncode == 0, f"STDERR:\n{res.stderr}\nSTDOUT:\n{res.stdout}"

    # Outputs exist under ./out
    out_dir = pkg_dir / "out"
    assert (out_dir / out_png).exists()

    # CSVs written
    csvs = list(out_dir.glob(f"{csv_prefix}_*.csv"))
    assert len(csvs) >= 3, f"expected several CSVs for zeta/wn/rays, got {len(csvs)}"
