
import math
import numpy as np
import sympy as sp
import pytest
from state_space.stateSpaceTool.io import parse_poly, polyz_to_zmin1

def test_parse_zmin1_normalizes_and_pads():
    b,a = parse_poly(num="0 1", den="2 1 0.5", form="zmin1", zeros=None, poles=None, gain=None)
    # First denominator coefficient should normalize to 1.0
    assert pytest.approx(a) == [0.5, 0.25]
    # Numerator should be padded to order n+1 = 3
    assert len(b) == 3

def test_parse_z_descending_powers():
    # H(z) = 1 / (z^2 + 1.3 z + 0.4)
    b,a = parse_poly(num="1 0 0", den="1 1.3 0.4", form="z", zeros=None, poles=None, gain=None)
    assert len(a) == 2 and len(b) == 3

def test_parse_expr_and_auto_equivalence():
    b1,a1 = parse_poly(num="z+1", den="z**2 + 1.3*z + 0.4", form="expr", zeros=None, poles=None, gain=None)
    b2,a2 = parse_poly(num="z+1", den="z**2 + 1.3*z + 0.4", form="auto", zeros=None, poles=None, gain=None)
    assert b1 == b2 and a1 == a2

def test_parse_zpk_roundtrip_simple():
    b,a = parse_poly(num=None, den=None, form="zpk", zeros="-1", poles="-0.5 -0.8", gain=1.0)
    assert len(a) == 2 and len(b) == 3

def test_polyz_to_zmin1_long_division_remainder():
    z = sp.symbols('z')
    # N(z)/D(z) with deg(N) >= deg(D) should be reduced by remainder
    b,a = polyz_to_zmin1(Nz=z**2, Dz=z**2 + 1.3*z + 0.4)
    assert len(a) == 2 and len(b) == 3
