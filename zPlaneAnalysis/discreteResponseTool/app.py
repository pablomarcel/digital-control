
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import numpy as np

from .apis import RunRequest
from .utils import with_outdir_policy
from .core import (cont2disc_zoh, pid_positional_q, analog_pid_to_positional_q,
                   make_controller_from_kwargs, series_q, feedback_cl_q, filt_lti_q,
                   step_metrics, poly_eval_q_at1, zroots_from_q, diophantine_place)
from .design import (pretty_q, pzmap, root_locus, plotly_step, plotly_pz, plotly_rlocus, panel_plot)

@dataclass
class SystemData:
    T: float
    G_num: np.ndarray
    G_den: np.ndarray
    Gd_num: np.ndarray
    Gd_den: np.ndarray
    plant_desc: str
    ctrl_desc: str

class DiscreteResponseApp:
    def __init__(self, request: RunRequest):
        self.req = request

    # -------- Build system --------
    def _build(self) -> SystemData:
        r = self.req
        if r.example37:
            T = 1.0
            G_num, G_den = cont2disc_zoh([1.0], [1.0, 1.0, 0.0], T)
            Gd_num, Gd_den = pid_positional_q(1.0, 0.2, 0.2)
            return SystemData(T, G_num, G_den, Gd_num, Gd_den, "Discrete", "Digital PID (positional)")
        if r.T is None or r.plant_num is None or r.plant_den is None:
            raise ValueError("Provide --T, --plant-num, --plant-den or use --example37")
        T = float(r.T)
        G_num, G_den = cont2disc_zoh(r.plant_num, r.plant_den, T)
        bqd, aqd, cdesc = make_controller_from_kwargs(T=T, Kp=r.Kp, Ki=r.Ki, Kd=r.Kd,
                                                      K=r.K, Ti=r.Ti, Td=r.Td,
                                                      ctrl_numz=r.ctrl_numz, ctrl_denz=r.ctrl_denz)
        if bqd is None or aqd is None:
            if r.cl_poles:
                bqd = np.array([1.0]); aqd = np.array([1.0]); cdesc = "unity (placeholder for placement)"
            else:
                raise ValueError("No controller specified. Use --Kp/--Ki/--Kd, or --K/--Ti/--Td, or --ctrl-numz/--ctrl-denz")
        return SystemData(T, G_num, G_den, bqd, aqd, "Discrete", cdesc)

    # -------- Run end-to-end --------
    @with_outdir_policy
    def run(self, *, matplotlib: Optional[str]=None, csv: Optional[str]=None, pzmap: Optional[str]=None,
            rlocus: Optional[str]=None, plotly_step: Optional[str]=None, plotly_pz: Optional[str]=None,
            plotly_rl: Optional[str]=None, panel: Optional[str]=None, outdir: str = "out") -> Dict:
        r = self.req
        data = self._build()

        # Open loop and T_loop
        numL_q, denL_q = series_q(data.Gd_num, data.Gd_den, data.G_num, data.G_den)
        numT_loop_q, denT_loop_q = feedback_cl_q(numL_q, denL_q)

        # Optional placement
        if r.cl_poles:
            A_des_z_desc = np.poly(r.cl_poles)  # descending z polynomial with desired roots
            A_des_q = np.array(A_des_z_desc, dtype=float)  # SAME order for q-ascending
            Bd, Ad = diophantine_place(data.G_num, data.G_den, A_des_q)
            data.Gd_num, data.Gd_den = Bd, Ad
            numL_q, denL_q = series_q(data.Gd_num, data.Gd_den, data.G_num, data.G_den)
            numT_loop_q, denT_loop_q = feedback_cl_q(numL_q, denL_q)

        # Two-DOF or 1-DOF with prefilter
        TL_dc = poly_eval_q_at1(numT_loop_q) / max(1e-15, poly_eval_q_at1(denT_loop_q))
        two = bool(r.two_dof)
        if two:
            if r.t_design == "custom":
                if r.t_numz is None or r.t_denz is None:
                    raise ValueError("--t-design custom requires both --t-numz and --t-denz")
                T_num, T_den = np.array(r.t_numz, float), np.array(r.t_denz, float)
            elif r.t_design == "lag":
                beta = float(r.t_beta)
                if not (0.0 < beta < 1.0): raise ValueError("--t-beta must be in (0,1)")
                k = 1.0 / (TL_dc if abs(TL_dc) > 1e-15 else 1.0)
                T_num = np.array([k*(1.0 - beta)], float); T_den = np.array([1.0, -beta], float)
            elif r.t_design == "none":
                T_num, T_den = np.array([1.0]), np.array([1.0])
            else:
                k = 1.0 / (TL_dc if abs(TL_dc) > 1e-15 else 1.0)
                T_num, T_den = np.array([k], float), np.array([1.0], float)
            num_effective_q, den_effective_q = series_q(T_num, T_den, numT_loop_q, denT_loop_q)
        else:
            num_effective_q, den_effective_q = numT_loop_q.copy(), denT_loop_q.copy()
            if r.pre_numz or r.pre_denz:
                F_num = np.array(r.pre_numz if r.pre_numz else [1.0], float)
                F_den = np.array(r.pre_denz if r.pre_denz else [1.0], float)
                num_effective_q, den_effective_q = series_q(F_num, F_den, num_effective_q, den_effective_q)

        # Input
        N = int(r.N)
        if r.input == "step":
            u = np.full(N, float(r.amp)); title = f"Step Response (N={N}, T={data.T})"
        else:
            slope = float(r.amp); u = slope * np.arange(N, dtype=float)
            title = f"Ramp Response (slope={slope}, N={N}, T={data.T})"

        y = filt_lti_q(num_effective_q, den_effective_q, u)
        k = np.arange(N)
        metrics = step_metrics(y) if r.input == "step" else None

        # CSV
        if csv:
            import csv as _csv
            with open(csv, "w", newline="") as f:
                w = _csv.writer(f); w.writerow(["k","u[k]","y[k]"])
                for i,(ui,yi) in enumerate(zip(u,y)): w.writerow([i, float(ui), float(yi)])

        # Plots
        if matplotlib:
            try:
                import matplotlib.pyplot as _mpl  # noqa
                fig_path = matplotlib
                import matplotlib.pyplot as plt
                fig, ax = plt.subplots(figsize=(7,4.5))
                ax.plot(k, y, '-o', ms=4)
                ax.set_title(title); ax.set_xlabel("k"); ax.set_ylabel("y[k]")
                if r.input=="step" and metrics:
                    if metrics.get("k_peak") is not None: ax.plot(metrics["k_peak"], y[metrics["k_peak"]], 'o', c='red')
                    if metrics.get("k_settle") is not None: ax.axvline(metrics["k_settle"], ls='--', c='green', alpha=0.6)
                ax.grid(True, ls=':', alpha=0.6)
                fig.savefig(fig_path, bbox_inches='tight', dpi=160); plt.close(fig)
            except Exception as e:
                print("[warn] matplotlib not available:", e)
        if pzmap:
            try:
                from .design import pzmap as _pz; _pz(num_effective_q, den_effective_q, path=pzmap, clip=float(self.req.pzclip),
                                                     title=("Ref→Out H(z)" if two else "Closed-loop T(z)"))
            except Exception as e:
                print("[warn] pzmap failed:", e)
        if rlocus:
            try:
                from .design import root_locus as _rl
                numL_rl, denL_rl = series_q(data.Gd_num, data.Gd_den, data.G_num, data.G_den)
                _rl(numL_rl, denL_rl, Kmin=float(r.kmin), Kmax=float(r.kmax), logscale=bool(r.rlocus_log),
                    rclip=float(r.rclip), path=rlocus)
            except Exception as e:
                print("[warn] rlocus failed:", e)
        if plotly_step:
            try:
                from .design import plotly_step as _ps; _ps(k, y, plotly_step, title=title)
            except Exception as e:
                print("[warn] plotly_step failed:", e)
        if plotly_pz:
            try:
                from .design import plotly_pz as _pp; _pp(num_effective_q, den_effective_q, plotly_pz, clip=float(r.pzclip))
            except Exception as e:
                print("[warn] plotly_pz failed:", e)
        if plotly_rl:
            try:
                from .design import plotly_rlocus as _prl
                numL_rl, denL_rl = series_q(data.Gd_num, data.Gd_den, data.G_num, data.G_den)
                _prl(numL_rl, denL_rl, plotly_rl, Kmin=float(r.kmin), Kmax=float(r.kmax),
                     logscale=bool(r.rlocus_log), rclip=float(r.rclip))
            except Exception as e:
                print("[warn] plotly_rl failed:", e)
        if panel:
            try:
                from .design import panel_plot as _panel
                _panel(k, y, num_effective_q, den_effective_q, numL_q, denL_q, path=panel,
                       rclip=float(r.rclip), pzclip=float(r.pzclip), metrics=(metrics if r.input=='step' else None))
            except Exception as e:
                print("[warn] panel failed:", e)

        return {
            "matplotlib": matplotlib, "csv": csv, "pzmap": pzmap, "rlocus": rlocus,
            "plotly_step": plotly_step, "plotly_pz": plotly_pz, "plotly_rl": plotly_rl, "panel": panel,
            "metrics": metrics, "y": y.tolist(), "k": k.tolist(),
        }
