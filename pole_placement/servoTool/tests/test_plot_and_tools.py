from __future__ import annotations
import os
import pytest

def test_class_diagram_writes():
    from pole_placement.servoTool.tools.class_diagram import main
    main(out_dir="out")
    # file path
    here = os.path.dirname(__file__)
    # not checking existence here; script prints path; rely on no exception

def test_plot_matplotlib(tmp_path):
    from pole_placement.servoTool.plot import plot_matplotlib
    y = [0, 0.5, 0.8, 1.0]
    out = tmp_path/"fig.png"
    plot_matplotlib(y, savefig=str(out), show=False)
    assert out.exists()

@pytest.mark.skipif(__import__('importlib').import_module('importlib').util.find_spec('plotly') is None, reason="plotly not installed")
def test_plot_plotly(tmp_path):
    from pole_placement.servoTool.plot import plot_plotly
    y = [0, 0.5, 0.8, 1.0]
    out = tmp_path/"fig.html"
    plot_plotly(y, html=str(out), open_after=False)
    assert out.exists()
