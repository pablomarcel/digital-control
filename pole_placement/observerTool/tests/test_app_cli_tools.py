
from __future__ import annotations
import json
import sys

from pole_placement.observerTool.app import ObserverApp
from pole_placement.observerTool.apis import DesignRequest, ClosedLoopRequest, K0Request, SelectRequest, SimRequest, ExampleRequest
from pole_placement.observerTool import cli
from pole_placement.observerTool.tools.class_diagram import main as classdiag_main

A = '1 0.2; 0 1'
B = '0.02; 0.2'
C = '1 0'
K = '8 3.2'
L = '2; 5'

def test_app_dispatch_and_examples(tmp_path):
    app = ObserverApp()
    out1 = app.run(DesignRequest(kind='prediction', A=A, C=C, poles='0,0', method='acker'))
    assert 'L' in out1
    out2 = app.run(ClosedLoopRequest(A=A, B=B, C=C, K=K, L=L))
    assert 'eig_augmented' in out2
    out3 = app.run(K0Request(A=A, B=B, C=C, K=K, L=L, mode='ogata', ogata_extra_gain=1.0))
    assert out3['K0'] > 0
    out4 = app.run(SelectRequest(A=A, B=B, C=C, K=K, rule_of_thumb='0.9,0.8'))
    assert 'L' in out4
    out5 = app.run(SimRequest(A=A, B=B, C=C, K=K, L=L, N=5, Ts=0.2))
    assert 'y' in out5
    for ex in ('6-9','6-10','6-11','6-12'):
        e = app.run(ExampleRequest(which=ex, Ts=0.2))
        assert isinstance(e, dict)

def test_cli_subcommands_run(monkeypatch, capsys, tmp_path):
    # design
    monkeypatch.setenv("PYTHONWARNINGS", "ignore")
    sys.argv = ["prog","design","--type","prediction","--A",A,"--C",C,"--poles","0,0","--method","acker"]
    cli.main()
    # closedloop
    sys.argv = ["prog","closedloop","--A",A,"--B",B,"--C",C,"--K",K,"--L",L]
    cli.main()
    # k0
    sys.argv = ["prog","k0","--A",A,"--B",B,"--C",C,"--K",K,"--L",L,"--mode","ogata","--ogata-extra-gain","1.0"]
    cli.main()
    # select
    sys.argv = ["prog","select","--A",A,"--B",B,"--C",C,"--K",K,"--rule-of-thumb","0.8,0.7"]
    cli.main()
    # sim
    sys.argv = ["prog","sim","--A",A,"--B",B,"--C",C,"--K",K,"--L",L,"--N","5","--Ts","0.2"]
    cli.main()

def test_tools_class_diagram(tmp_path, monkeypatch):
    # ensure it writes without error
    classdiag_main("out")
