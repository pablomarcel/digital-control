import os, tempfile
from intro.vcdTool.apis import RunRequest
from intro.vcdTool.app import VCDApp

SIMPLE_VCD = """
$date today $end
$version gen $end
$timescale 1 us $end
$scope module top $end
$var wire 1 ! clk $end
$var wire 1 " a $end
$enddefinitions $end
#0
0!
0"
#1
1!
#2
0!
#3
1!
"""

def test_app_runs_and_writes_png(tmp_path, monkeypatch):
    vcd_path = tmp_path / "s.vcd"
    vcd_path.write_text(SIMPLE_VCD)
    # run with explicit paths to keep test isolated
    req = RunRequest(
        vcd=str(vcd_path),
        signals=["clk","a"],
        png=str(tmp_path / "out.png"),
        backend="mpl",
        in_dir=str(tmp_path),
        out_dir=str(tmp_path),
    )
    res = VCDApp().run(req)
    assert os.path.exists(res["out"]["png"])
