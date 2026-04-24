
from introduction.adcTool.utils import fmt_code, bin_zero_padded
def test_fmt_code_all():
    s = fmt_code(10, nbits=8, radix='all')
    assert "0b" in s and "0x" in s
    assert bin_zero_padded(3, 5) == "00011"
