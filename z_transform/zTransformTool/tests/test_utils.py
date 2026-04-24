# -*- coding: utf-8 -*-
import os
import sympy as sp
from z_transform.zTransformTool import utils

def test_symbol_table_contents():
    syms = utils.symbol_table()
    for k in ["k","z","T","w","a","b","t","I"]:
        assert k in syms
    assert syms["k"].is_integer
    assert syms["k"].is_nonnegative

def test_ensure_and_force_out_path_relative_maps_into_package_out(tmp_path):
    # relative → package out/
    rel = "myseq.csv"
    mapped = utils.force_out_path(rel)
    assert os.path.basename(mapped) == "myseq.csv"
    assert os.path.isdir(os.path.dirname(mapped))
    # absolute respected
    abs_target = os.path.join(str(tmp_path), "abs.csv")
    mapped_abs = utils.force_out_path(abs_target)
    assert mapped_abs == abs_target

def test_pbox_formats_plain_and_latex():
    s = utils.pbox("Title", sp.Symbol('x') + 1, latex=False)
    # pretty box uses '=' lines; just check essential content is present
    assert "Title" in s
    assert "x + 1" in s
    assert "=" in s  # underline line

    s2 = utils.pbox("Title", sp.Symbol('x') + 1, latex=True)
    # latex output can vary by sympy version; check it's non-empty and mentions x
    assert "x" in s2 or "\\mathrm" in s2
