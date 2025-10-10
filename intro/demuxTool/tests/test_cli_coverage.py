from __future__ import annotations
import os, io, contextlib
from intro.demuxTool import cli

def test_cli_main_with_inline_json_and_outdirs(tmp_path, monkeypatch):
    argv = [
        "--json", '[{\"sel\":0,\"x\":1},{\"sel\":1,\"x\":3},{\"sel\":2,\"x\":7}]',
        "--n", "4",
        "--bits", "8",
        "--out", "r.csv",
        "--trace", "r.vcd",
        "--in-dir", str(tmp_path / "in"),
        "--out-dir", str(tmp_path / "out"),
    ]
    # capture stdout so test doesn't spam
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = cli.main(argv)
    assert rc == 0
    assert (tmp_path / "out" / "r.csv").exists()
    assert (tmp_path / "out" / "r.vcd").exists()
    out = buf.getvalue().lower()
    assert "wrote results csv" in out
    assert "wrote vcd wavefile" in out

def test_cli_errors_without_inputs():
    # Expect argparse to error out; simulate by calling main with no args and intercept SystemExit
    try:
        cli.main([])
    except SystemExit as e:
        # argparse uses exit code 2 for parsing errors
        assert e.code != 0
    else:
        raise AssertionError("cli.main should have exited with error when no inputs provided")
