import os
from intro.vcdTool import cli

# We'll monkeypatch the app runner so we don't depend on plotting libs here
def fake_run(self, req):
    # Return a manifest-like dict that cli expects
    return {"vcd": req.vcd, "signals": req.signals or [], "out": {"png": req.png, "html": req.html, "csv": req.out_csv}}

SIMPLE_VCD = '''
$date $end
$timescale 1 us $end
$scope module t $end
$var wire 1 ! clk $end
$upscope $end
$enddefinitions $end
#0
0!
#1
1!
'''

def test_cli_mpl_main(tmp_path, monkeypatch, capsys):
    vcd = tmp_path / "x.vcd"
    vcd.write_text(SIMPLE_VCD)
    monkeypatch.setattr("intro.vcdTool.app.VCDApp.run", fake_run, raising=False)
    argv = [str(vcd), "--signals", "clk", "--png", str(tmp_path/"o.png"), "--in-dir", str(tmp_path), "--out-dir", str(tmp_path)]
    cli.main(argv)
    out = capsys.readouterr().out
    assert "=== vcdTool manifest ===" in out

def test_cli_plotly_main(tmp_path, monkeypatch):
    vcd = tmp_path / "x.vcd"
    vcd.write_text(SIMPLE_VCD)
    monkeypatch.setattr("intro.vcdTool.app.VCDApp.run", fake_run, raising=False)
    argv = [str(vcd), "--signals", "clk", "--backend", "plotly", "--html", str(tmp_path/"o.html"), "--in-dir", str(tmp_path), "--out-dir", str(tmp_path)]
    cli.main(argv)
