from introduction.vcdTool.core import VCDParser, WaveformBuilder, Decoder

VCD = '''
$date $end
$timescale 1 ns $end
$scope module t $end
$var wire 2 # code $end
$var wire 1 ! clk $end
$upscope $end
$enddefinitions $end
#0
0!
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
'''

def test_decoder_adds_bit_series(tmp_path):
    p = tmp_path / "d.vcd"
    p.write_text(VCD)
    vcd = VCDParser().parse(str(p))
    times, series, raw, widths = WaveformBuilder().build(vcd, ["clk","code"])
    Decoder().apply(series, raw, widths, [("code", 2)])
    assert "code[0]" in series and "code[1]" in series
    assert len(series["code[0]"]) == 4
