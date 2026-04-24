# -*- coding: utf-8 -*-
from z_transform.zTransformTool import cli

def test_cli_has_expected_flags():
    p = cli.build_parser()
    helptext = p.format_help()
    for flag in ["--z", "--zt", "--iz", "--series", "--residuez", "--tf", "--diff"]:
        assert flag in helptext
    for opt in ["--expr","--xt","--X","--subs","--N","--export_csv","--export_json"]:
        assert opt in helptext
