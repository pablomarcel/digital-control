import os, numpy as np
from quadraticControl.quadraticTool.design import plot_series_mpl, plot_series_plotly

def test_plot_helpers(tmp_path):
    series = {"x": np.arange(5), "u": np.linspace(0,1,5)}
    out_png = tmp_path / "fig.png"
    out_html = tmp_path / "fig.html"
    plot_series_mpl(series, "demo", str(out_png))
    plot_series_plotly(series, "demo", str(out_html))
    assert os.path.exists(out_png) and os.path.getsize(out_png) > 0
    assert os.path.exists(out_html) and os.path.getsize(out_html) > 0
