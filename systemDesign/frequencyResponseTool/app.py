# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from typing import List, Tuple

import numpy as np

from .apis import (
    RunRequest, RunResult, RunFiles, Margins,
    LeadParams, LagParams, LagLeadParams
)
from .design import make_nu_grid, bode_from_asc, compute_margins, MatplotlibPlotter, PlotlyPlotter
from .core import (
    z_to_w, Lead, Lag, LagLead,
    lead_w_to_z, lag_w_to_z, laglead_w_to_z,
    series_desc, closed_loop_desc, step_response_csv, auto_lead
)
from .utils import ensure_dir

class FrequencyResponseApp:
    def __init__(self) -> None:
        pass

    def _choose_compensator(self, req: RunRequest, Gw_num, Gw_den):
        corners: List[tuple[float,str]] = []
        comp_w = (np.array([1.0]), np.array([1.0]))
        comp_z = ([1.0], [1.0])
        chosen = None

        if req.mode == "none":
            chosen = "none"

        elif req.mode == "lead" and req.lead:
            prm = Lead(req.lead.K, req.lead.alpha, req.lead.tau)
            comp_w = prm.to_w()
            comp_z = lead_w_to_z(prm, req.T)
            corners += [(1.0/prm.tau, "zero 1/τ"), (1.0/(prm.alpha*prm.tau), "pole 1/(ατ)")]
            chosen = "lead"

        elif req.mode == "lag" and req.lag:
            prm = Lag(req.lag.K, req.lag.beta, req.lag.tau)
            comp_w = prm.to_w()
            comp_z = lag_w_to_z(prm, req.T)
            corners += [(1.0/prm.tau, "zero 1/τ"), (1.0/(prm.beta*prm.tau), "pole 1/(βτ)")]
            chosen = "lag"

        elif req.mode == "laglead" and req.laglead:
            prm = LagLead(req.laglead.K, req.laglead.beta, req.laglead.tau_lag, req.laglead.alpha, req.laglead.tau_lead)
            comp_w = prm.to_w()
            comp_z = laglead_w_to_z(prm, req.T)
            corners += [(1.0/req.laglead.tau_lag, "lag z 1/τlag"),
                        (1.0/(req.laglead.beta*req.laglead.tau_lag), "lag p 1/(βτlag)"),
                        (1.0/req.laglead.tau_lead, "lead z 1/τlead"),
                        (1.0/(req.laglead.alpha*req.laglead.tau_lead), "lead p 1/(ατlead)")]
            chosen = "laglead"

        elif req.mode == "auto":
            lead_auto = auto_lead(Gw_num, Gw_den, req.T, req.pm_req, req.gm_req, req.Kv_req)
            comp_w = lead_auto.to_w()
            comp_z = lead_w_to_z(lead_auto, req.T)
            corners += [(1.0/lead_auto.tau, "zero 1/τ"), (1.0/(lead_auto.alpha*lead_auto.tau), "pole 1/(ατ)")]
            chosen = "auto"

        else:
            raise ValueError("Invalid compensator configuration for mode: " + str(req.mode))

        return chosen, comp_w, comp_z, corners

    def run(self, req: RunRequest) -> RunResult:
        ensure_dir(req.out_dir)

        # map plant G(z) -> G(w)
        Gw_num, Gw_den = z_to_w(req.gz_num_desc, req.gz_den_desc, req.T)

        mode, (Gdw_num, Gdw_den), (Gdz_num, Gdz_den), corners = self._choose_compensator(req, Gw_num, Gw_den)

        # open-loop and closed-loop in z
        L_num, L_den = series_desc(Gdz_num, Gdz_den, req.gz_num_desc, req.gz_den_desc)
        CL_num, CL_den = closed_loop_desc(L_num, L_den)

        # frequency responses (Gw, Gdw, open-loop)
        nu = make_nu_grid(req.T)
        Gw_mag, Gw_ph   = bode_from_asc(Gw_num, Gw_den, nu)
        Gdw_mag, Gdw_ph = bode_from_asc(Gdw_num, Gdw_den, nu)
        OL_mag, OL_ph   = bode_from_asc(np.polynomial.polynomial.polymul(Gdw_num, Gw_num),
                                        np.polynomial.polynomial.polymul(Gdw_den, Gw_den), nu)
        margins: Margins = compute_margins(nu, OL_mag, OL_ph)

        files: list[RunFiles] = []
        # plotting
        if req.use_mpl and req.save_mpl:
            mpl = MatplotlibPlotter(save_pngs=True)
            for title, mag, ph, name, corner_flag, margin_flag in [
                ("Plant G(w)", Gw_mag, Gw_ph, "bode_Gw_mpl.png", False, False),
                ("Compensator Gd(w)", Gdw_mag, Gdw_ph, "bode_Gdw_mpl.png", True, False),
                ("Open-loop Gd(w)G(w)", OL_mag, OL_ph, "bode_OLw_mpl.png", True, True),
            ]:
                dst = os.path.join(req.out_dir, name)
                mpl.bode(nu, mag, ph, title, dst,
                         corners=corners if corner_flag else None,
                         margins=margins if margin_flag else None)
                files.append(RunFiles(dst, f"Matplotlib Bode: {title}"))

        if req.use_plotly:
            ply = PlotlyPlotter()
            for title, mag, ph, stem, corner_flag, margin_flag in [
                ("Plant G(w)", Gw_mag, Gw_ph, "bode_Gw", False, False),
                ("Compensator Gd(w)", Gdw_mag, Gdw_ph, "bode_Gdw", True, False),
                ("Open-loop Gd(w)G(w)", OL_mag, OL_ph, "bode_OLw", True, True),
            ]:
                dst = os.path.join(req.out_dir, f"{stem}.{req.plotly_fmt.lower()}")
                ply.bode(nu, mag, ph, title, dst, req.plotly_fmt,
                         corners=corners if corner_flag else None,
                         margins=margins if margin_flag else None)
                files.append(RunFiles(dst, f"Plotly Bode: {title} ({req.plotly_fmt})"))

        # optional step CSV
        if req.step_N and req.step_N > 0:
            csv_path = os.path.join(req.out_dir, "step.csv")
            step_response_csv(CL_num, CL_den, req.T, req.step_N, csv_path)
            files.append(RunFiles(csv_path, "Unit-step response of C(z)/R(z)"))

        return RunResult(
            Gd_w_num_asc=[float(x) for x in Gdw_num],
            Gd_w_den_asc=[float(x) for x in Gdw_den],
            Gd_z_num_desc=[float(x) for x in Gdz_num],
            Gd_z_den_desc=[float(x) for x in Gdz_den],
            L_num_desc=[float(x) for x in L_num],
            L_den_desc=[float(x) for x in L_den],
            CL_num_desc=[float(x) for x in CL_num],
            CL_den_desc=[float(x) for x in CL_den],
            margins=margins,
            files=files
        )
