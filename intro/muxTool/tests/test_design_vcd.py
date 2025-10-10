
import re, os
from intro.muxTool.design import write_vcd

def test_write_vcd_generates_content(tmp_path):
    rows = [
        {"cycle":0,"sel":0,"d0":1,"d1":2,"d2":3,"d3":4,"y":1},
        {"cycle":1,"sel":1,"d0":5,"d1":6,"d2":7,"d3":8,"y":6},
    ]
    outp = tmp_path / "waves" / "mux.vcd"
    write_vcd(str(outp), rows, data_bw=8, timescale='10ns')
    text = outp.read_text()
    assert "$timescale 10ns $end" in text
    assert re.search(r"\$var wire 2 s sel \$end", text) is not None
    assert "#0" in text or "#10" in text
