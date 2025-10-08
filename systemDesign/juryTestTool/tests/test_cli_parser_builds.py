
from systemDesign.juryTestTool.cli import build_parser

def test_cli_build_parser_and_parse():
    p = build_parser()
    ns = p.parse_args(["--coeffs","1, -1.2, 0.07, 0.3, -0.08","--method","jury"])
    assert ns.method == "jury"
