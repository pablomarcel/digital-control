
from __future__ import annotations
from intro.dacTool.cli import build_parser

def test_cli_parsing_weighted():
    p = build_parser()
    ns = p.parse_args(["weighted","--csv","codes.csv","--nbits","3","--vref","2.5","--gain","1.0","--vcd-ideal"])
    assert ns.mode == "weighted"
    assert ns.include_ideal_in_vcd is True

def test_cli_parsing_r2r():
    p = build_parser()
    ns = p.parse_args(["r2r","--csv","codes.csv","--nbits","3","--vref","3.3","--R","10000","--sigma-r-pct","0.1","--sigma-2r-pct","0.2"])
    assert ns.mode == "r2r"
    assert ns.R_ohm == 10000.0
