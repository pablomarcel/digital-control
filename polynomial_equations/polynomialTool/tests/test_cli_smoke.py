
import sys, types, os, json
from polynomial_equations.polynomialTool import cli as cli_mod

def run_cli(argv):
    old = sys.argv[:]
    try:
        sys.argv = argv
        cli_mod.main()
    finally:
        sys.argv = old

def test_cli_solve(capsys):
    run_cli(['cli.py','solve','--A','1,1,0.5','--B','1,2','--D','1,0,0,0','--layout','ogata'])
    out = capsys.readouterr().out
    assert 'alpha:' in out and 'beta :' in out

def test_cli_polydesign(capsys, tmp_path):
    run_cli(['cli.py','polydesign','--A','1,-2,1','--B','0.02,0.02','--H','1,-1.2,0.52','--F','1,0','--config','2','--backend','none','--kmax','5'])
    out = capsys.readouterr().out
    assert 'alpha:' in out

def test_cli_rst(capsys):
    run_cli(['cli.py','rst','--A','1,-2,1','--B','0.02,0.02','--H','1,-1.2,0.52','--F','1,0','--backend','none'])
    out = capsys.readouterr().out
    assert 'alpha:' in out

def test_cli_modelmatch(capsys):
    run_cli(['cli.py','modelmatch','--A','1,-1.3679,0.3679','--B','0.3679,0.2642','--Gmodel_num','0.62,-0.3','--Gmodel_den','1,-1.2,0.52','--H1','1,0.5','--F','1,0','--backend','none'])
    out = capsys.readouterr().out
    assert 'alpha:' in out
