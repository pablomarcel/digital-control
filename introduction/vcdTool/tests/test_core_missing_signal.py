import pytest
from introduction.vcdTool.core import VCDParser, WaveformBuilder

VCD = '''
$date $end
$timescale 1 us $end
$scope module t $end
$var wire 1 ! clk $end
$upscope $end
$enddefinitions $end
#0
0!
'''

def test_missing_signal_raises(tmp_path):
    p = tmp_path / "m.vcd"
    p.write_text(VCD)
    vcd = VCDParser().parse(str(p))
    with pytest.raises(ValueError):
        WaveformBuilder().build(vcd, ["clk","nope"])
