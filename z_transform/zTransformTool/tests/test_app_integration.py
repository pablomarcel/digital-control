# -*- coding: utf-8 -*-
import sympy as sp
import numpy as np
import pytest

from z_transform.zTransformTool.app import ZTApp
from z_transform.zTransformTool.apis import RunRequest

def test_app_forward_and_series_and_inverse_smokes():
    app = ZTApp(print_boxes=False)

    # forward z
    out = app.run(RunRequest(mode="forward", expr="sin(w*T*k)", subs="T=1,w=0.5"))
    assert "Xz" in out

    # series
    out2 = app.run(RunRequest(mode="series", X="z**-1/(1+z**-1)", N=5))
    assert len(out2["coeffs"]) == 6

    # inverse with N
    out3 = app.run(RunRequest(mode="inverse", X="1 + 2*z**-1 + 3*z**-2 + 4*z**-3", N=5))
    assert out3["seq"][:3] == [1,2,3]

def test_app_residuez_smoke():
    app = ZTApp(print_boxes=False)
    out = app.run(RunRequest(mode="residuez", num="0 0.5 -0.25", den="1 -1.2 0.36"))
    assert "r" in out and "p" in out

@pytest.mark.parametrize("control_available", [True, False])
def test_app_tf_optional_monkeypatch(control_available, monkeypatch):
    # If python-control is available, run impulse; otherwise expect RuntimeError from core.tf_util
    app = ZTApp(print_boxes=False)
    if not control_available:
        import z_transform.zTransformTool.core as core
        monkeypatch.setattr(core, "ct", None, raising=True)
        with pytest.raises(RuntimeError):
            app.run(RunRequest(mode="tf", num="0 0.5 -0.25", den="1 -1.2 0.36", impulse=True, N=5))
    else:
        out = app.run(RunRequest(mode="tf", num="0 0.5 -0.25", den="1 -1.2 0.36", impulse=True, N=5))
        assert "impulse_y" in out
