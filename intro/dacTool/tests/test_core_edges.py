
from __future__ import annotations
from intro.dacTool.core import WeightedDAC, R2RDAC

def test_weighted_with_mismatch_seed():
    d1 = WeightedDAC(nbits=3, vref=1.0, ro_over_r=1.0, res_sigma_pct=0.5, seed=123)
    d2 = WeightedDAC(nbits=3, vref=1.0, ro_over_r=1.0, res_sigma_pct=0.5, seed=123)
    bits = [1,0,1]
    assert abs(d1.vo_nonideal_bits(bits) - d2.vo_nonideal_bits(bits)) < 1e-12

def test_r2r_nonideal_path_monotonic_small():
    d = R2RDAC(nbits=3, vref=1.0, R_ohm=10000.0, sigma_r_pct=0.1, sigma_2r_pct=0.1, seed=42)
    last = -1.0
    for code in range(8):
        bits = [(code >> i) & 1 for i in range(3)]
        vo = d.vo_nonideal_bits(bits)
        assert vo >= last - 1e-9
        last = vo
