import os
from intro.vcdTool.apis import RunRequest
from intro.vcdTool.app import VCDApp
import intro.vcdTool.design as design

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

def test_app_plotly_branch_and_csv(tmp_path, monkeypatch):
    vcd = tmp_path / "a.vcd"
    vcd.write_text(SIMPLE_VCD)

    # Bypass real plotly by replacing plot_plotly with a no-op
    monkeypatch.setattr(design, "plot_plotly", lambda *a, **k: None)

    req = RunRequest(
        vcd=str(vcd),
        signals=["clk"],
        backend="plotly",
        html=str(tmp_path / "o.html"),
        out_csv=str(tmp_path / "o.csv"),
        in_dir=str(tmp_path),
        out_dir=str(tmp_path),
    )
    res = VCDApp().run(req)
    assert os.path.exists(res["out"]["csv"])
