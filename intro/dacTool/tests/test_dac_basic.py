from __future__ import annotations
import json, os, sys, tempfile
from intro.dacTool.core import WeightedDAC, R2RDAC

def test_weighted_ideal_matches_formula():
    dac = WeightedDAC(nbits=4, vref=4.0, ro_over_r=1.0)
    # Code 0b1010 (LSB..MSB bits: [0,1,0,1])
    bits = [0,1,0,1]
    # Ideal weights (MSB..LSB = 1,1/2,1/4,1/8) -> LSB..MSB = [1/8,1/4,1/2,1]
    vo = dac.vo_ideal_bits(bits)
    # sum = 1/4 + 1 = 1.25 -> *4.0 = 5.0
    assert abs(vo - 5.0) < 1e-12

def test_r2r_ideal_monotonic():
    dac = R2RDAC(nbits=3, vref=3.0, R_ohm=10_000.0)
    # iterate codes 0..7
    last = -1.0
    for code in range(8):
        bits = [(code >> i) & 1 for i in range(3)]
        vo = dac.vo_ideal_bits(bits)
        assert vo >= last - 1e-12
        last = vo
