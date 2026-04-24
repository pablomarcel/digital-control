# -*- coding: utf-8 -*-
import sympy as sp
from z_transform.zTransformTool import core
from z_transform.zTransformTool.utils import symbol_table

def test_forward_sin():
    syms = symbol_table()
    xk, XZ = core.forward_z("sin(w*T*k)", syms, subs={"T":1.0, "w":0.5})
    assert XZ.free_symbols.issuperset({syms["z"]})
    # Just verify expression contains z symbol and doesn't error

def test_series_simple():
    syms = symbol_table()
    ser, coeffs = core.series_in_u("z**-1/(1 + z**-1)", syms, 6)
    assert len(coeffs) == 7
