# -*- coding: utf-8 -*-
import os, json, tempfile, shutil
import numpy as np

from systemDesign.frequencyResponseTool.apis import RunRequest, LeadParams, LagParams, LagLeadParams
from systemDesign.frequencyResponseTool.app import FrequencyResponseApp

PLANT = {
    "T": 0.2,
    "gz_num": [0.01873, 0.01752],
    "gz_den": [1.0, -1.8187, 0.8187],
}

def _run(req: RunRequest):
    app = FrequencyResponseApp()
    res = app.run(req)
    # sanity
    assert isinstance(res.Gd_z_den_desc, list)
    assert len(res.L_den_desc) >= 1
    return res

def test_app_none(tmp_path):
    out = tmp_path / "out"
    req = RunRequest(
        T=PLANT["T"], gz_num_desc=PLANT["gz_num"], gz_den_desc=PLANT["gz_den"],
        mode="none",
        use_plotly=True, plotly_fmt="html", out_dir=str(out)
    )
    res = _run(req)
    # at least 1 plot file generated
    assert any(os.path.exists(f.path) for f in res.files)

def test_app_lead_and_step(tmp_path):
    out = tmp_path / "out"
    req = RunRequest(
        T=PLANT["T"], gz_num_desc=PLANT["gz_num"], gz_den_desc=PLANT["gz_den"],
        mode="lead", lead=LeadParams(K=1.0, alpha=0.361, tau=0.979),
        use_plotly=True, plotly_fmt="html", step_N=20, out_dir=str(out)
    )
    res = _run(req)
    # step.csv present
    assert any(f.path.endswith("step.csv") for f in res.files)

def test_app_lag(tmp_path):
    out = tmp_path / "out"
    req = RunRequest(
        T=PLANT["T"], gz_num_desc=PLANT["gz_num"], gz_den_desc=PLANT["gz_den"],
        mode="lag", lag=LagParams(K=1.7, beta=4.0, tau=0.5),
        use_plotly=False, out_dir=str(out)
    )
    res = _run(req)
    assert isinstance(res.margins.nu_gc, (float, type(None)))

def test_app_laglead(tmp_path):
    out = tmp_path / "out"
    req = RunRequest(
        T=PLANT["T"], gz_num_desc=PLANT["gz_num"], gz_den_desc=PLANT["gz_den"],
        mode="laglead", laglead=LagLeadParams(K=1.0, beta=4.0, tau_lag=0.8, alpha=0.4, tau_lead=0.2),
        use_plotly=False, out_dir=str(out)
    )
    res = _run(req)
    assert len(res.Gd_w_num_asc) >= 2

def test_app_auto(tmp_path):
    out = tmp_path / "out"
    req = RunRequest(
        T=PLANT["T"], gz_num_desc=PLANT["gz_num"], gz_den_desc=PLANT["gz_den"],
        mode="auto", pm_req=50, gm_req=10, Kv_req=2.0,
        use_plotly=False, out_dir=str(out)
    )
    res = _run(req)
    assert len(res.Gd_z_num_desc) == 2 or len(res.Gd_z_num_desc) == 3  # SISO 1st/2nd order comp in z
