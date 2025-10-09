
import sys
import types
import pathlib
import builtins
import pytest

# Import the CLI module via absolute package path
from polePlacement.observabilityTool import cli as obsv_cli

def run_cli_argv(argv):
    """Helper to run cli.main() with a custom argv and capture SystemExit code."""
    old_argv = sys.argv
    try:
        sys.argv = argv
        with pytest.raises(SystemExit) as e:
            obsv_cli.main()
    finally:
        sys.argv = old_argv
    return e.value.code

def test_cli_observable(tmp_path, monkeypatch):
    # Observable DT case => exit code 0
    code = run_cli_argv([
        "cli.py",
        "--A", "-1 0; 0 -2",
        "--C", "1 5",
        "--discrete",
        "--name", "cli_obs",
        "--save-json"
    ])
    assert code == 0
    # summary JSON should be in package out/
    from polePlacement.observabilityTool.utils import pkg_outdir
    out = pathlib.Path(pkg_outdir()) / "cli_obs_summary.json"
    assert out.exists()

def test_cli_unobservable(tmp_path):
    # Unobservable DT case => exit code 2
    code = run_cli_argv([
        "cli.py",
        "--A", "-1 0; 0 -2",
        "--C", "0 1",
        "--discrete",
        "--name", "cli_unobs"
    ])
    assert code == 2
