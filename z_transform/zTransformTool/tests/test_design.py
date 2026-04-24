# -*- coding: utf-8 -*-
import sympy as sp
from z_transform.zTransformTool import design

def test_box_and_as_text():
    s = design.box("Hello", sp.Symbol('x')**2)
    assert "Hello" in s
    t = design.as_text(sp.Symbol('y')+1, latex=False)
    assert "y" in t
    t2 = design.as_text(sp.Symbol('y')+1, latex=True)
    assert "y" in t2 or "\\mathrm" in t2
