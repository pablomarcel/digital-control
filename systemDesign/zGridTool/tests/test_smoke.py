# -*- coding: utf-8 -*-
import math
from systemDesign.zGridTool.core import spiral_const_zeta
from systemDesign.zGridTool.apis import RunRequest
from systemDesign.zGridTool.app import ZGridApp

def test_spiral_basic():
    x, y = spiral_const_zeta(0.5, math.pi)
    assert len(x) == len(y)
    assert abs(x[0]-1.0) < 1e-9  # r(0)=1

def test_app_mpl_smoke(tmp_path):
    app = ZGridApp()
    req = RunRequest(T=0.05, backend="mpl", png="test.png", verbose=False)
    out = app.run(req)
    assert out.png_path and out.png_path.endswith("test.png")
