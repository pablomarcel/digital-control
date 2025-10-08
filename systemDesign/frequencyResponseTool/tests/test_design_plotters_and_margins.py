# -*- coding: utf-8 -*-
import os, json
import numpy as np

from systemDesign.frequencyResponseTool.design import (
    make_nu_grid, bode_from_asc, compute_margins, MatplotlibPlotter, PlotlyPlotter
)

def test_make_nu_grid():
    nu = make_nu_grid(0.2, nu_min=1e-2, nu_max=1.0, pdec=10)
    assert nu[0] > 0 and nu[-1] <= 1.0

def test_bode_and_margins_and_plotters(tmp_path):
    # simple first-order low-pass H(jw) = 1/(1+jw)
    num = [1.0]
    den = [1.0, 1.0]
    nu = np.logspace(-2, 2, 256)
    mag, ph = bode_from_asc(num, den, nu)
    margins = compute_margins(nu, mag, ph)
    # margins should be finite-ish for this system
    assert isinstance(margins.pm_deg, (float, type(None)))

    # Matplotlib (PNG) and Plotly (HTML) smoke
    png = tmp_path / "bode.png"
    html = tmp_path / "bode.html"
    mpl = MatplotlibPlotter()
    mpl.bode(nu, mag, ph, "Test", str(png))
    assert png.exists() and png.stat().st_size > 0

    ply = PlotlyPlotter()
    ply.bode(nu, mag, ph, "Test", str(html), "html")
    assert html.exists() and html.stat().st_size > 0
