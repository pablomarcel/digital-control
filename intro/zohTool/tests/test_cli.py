from __future__ import annotations
import os, io
from contextlib import redirect_stdout
from pathlib import Path

from intro.zohTool import cli

def _chdir_to_pkg():
    # change into the package dir so the cli import-shim path math mirrors real use
    pkg_dir = Path(__file__).resolve().parents[1]
    os.chdir(pkg_dir)

def test_cli_runs_with_inline_json_and_vcd(tmp_path, monkeypatch):
    _chdir_to_pkg()
    outdir = tmp_path / "out"
    outdir.mkdir(parents=True, exist_ok=True)
    argv = ["--json", "[0,1,2]", "--Ts", "0.1", "--trace", "z.vcd", "--out", "r.csv", "--out-dir", str(outdir)]
    f = io.StringIO()
    with redirect_stdout(f):
        rc = cli.main(argv)
    assert rc == 0
    # outputs should land under outdir
    assert (outdir / "z.vcd").exists()
    assert (outdir / "r.csv").exists()
    s = f.getvalue()
    assert "ZOH with Ts=0.1 s" in s

def test_cli_runs_with_csv_and_idx_bits(tmp_path, monkeypatch):
    _chdir_to_pkg()
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir(); out_dir.mkdir()
    (in_dir / "u.csv").write_text("u\n0\n0.5\n")
    argv = ["--csv", "u.csv", "--Ts", "0.2", "--idx-bits", "5", "--trace", "t.vcd", "--in-dir", str(in_dir), "--out-dir", str(out_dir)]
    rc = cli.main(argv)
    assert rc == 0
    assert (out_dir / "t.vcd").exists()

def test_cli_error_when_no_source(monkeypatch):
    _chdir_to_pkg()
    # Build parser and ensure mutually exclusive source is enforced
    parser = cli.build_parser()
    try:
        parser.parse_args([])
        assert False, "Expected SystemExit due to missing required args"
    except SystemExit:
        assert True
