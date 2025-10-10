import sys
from importlib import reload

def run_cli_argv(argv):
    sys_argv_bak = sys.argv[:]
    try:
        sys.argv = argv
        from stateSpace.liapunovTool import cli
        reload(cli)
        cli.main()
    finally:
        sys.argv = sys_argv_bak

def test_cli_ct(capsys):
    run_cli_argv(["cli.py", "ct", "--A", "[[0 1]; [-25 -4]]", "--Q", "[[1 0]; [0 1]]"])
    out = capsys.readouterr().out
    assert "Results" in out
    assert "definiteness" in out

def test_cli_example_dt(capsys):
    run_cli_argv(["cli.py", "example", "ogata_5_9", "--latex"])
    out = capsys.readouterr().out
    assert "LaTeX" in out
