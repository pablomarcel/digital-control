import os
from introduction.vcdTool.design import plot_mpl

def test_plot_mpl_digital_and_analog(tmp_path):
    times = [0.0, 1.0, 2.0]
    series = {"bit":[0,1,0], "ana":[0.0,0.5,1.2]}
    widths = {"bit":1, "ana":16}
    out = tmp_path / "p.png"
    plot_mpl(str(out), times, series, widths, "us", "t")
    assert out.exists()
