
from zPlaneAnalysis.discreteResponseTool.io import parse_coeffs, parse_complex_list

def test_parse_coeffs_and_complex():
    c = parse_coeffs(["1", "1e-3", "0.5"])
    assert c == [1.0, 1e-3, 0.5]
    z = parse_complex_list(["0.8", "0.7+0.2j", "0.7-0.2j"])
    assert len(z) == 3 and abs(z[1].imag-0.2) < 1e-9
