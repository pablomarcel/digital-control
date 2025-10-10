import os, tempfile
from intro.vcdTool.core import VCDParser, WaveformBuilder

SIMPLE_VCD = """
$date today $end
$version gen $end
$timescale 1 us $end
$scope module top $end
$var wire 1 ! clk $end
$var wire 1 " a $end
$var wire 2 # b $end
$upscope $end
$enddefinitions $end
#0
0!
0"
b00 #
#1
1!
b01 #
#2
0!
b10 #
#3
1!
b11 #
"""

def test_parse_and_build_minimal(tmp_path):
    p = tmp_path / "simple.vcd"
    p.write_text(SIMPLE_VCD)
    vcd = VCDParser().parse(str(p))
    assert abs(vcd.timescale_factor - 1e-6) < 1e-12
    assert any(v.name == "clk" for v in vcd.vars_by_id.values())
    times, series, rawbits, widths = WaveformBuilder().build(vcd, ["clk","a","b"])
    assert times == [0,1,2,3]
    assert series["clk"] == [0,1,0,1]
    assert series["b"] == [0,1,2,3]
