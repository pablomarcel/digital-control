
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse, os, sys

# ---------- Import shim so `python cli.py` works with absolute imports ----------
if __package__ in (None, ""):
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    from zPlaneAnalysis.discreteResponseTool.apis import RunRequest
    from zPlaneAnalysis.discreteResponseTool.app import DiscreteResponseApp
else:
    from .apis import RunRequest
    from .app import DiscreteResponseApp

def main():
    ap = argparse.ArgumentParser(description="Discrete-time response / z-plane toolbox (OO)")
    ap.add_argument("--example37", action="store_true")
    ap.add_argument("--plant-num", type=float, nargs="+", dest="plant_num")
    ap.add_argument("--plant-den", type=float, nargs="+", dest="plant_den")
    ap.add_argument("--T", type=float)
    ap.add_argument("--Kp", type=float); ap.add_argument("--Ki", type=float); ap.add_argument("--Kd", type=float)
    ap.add_argument("--K", type=float); ap.add_argument("--Ti", type=float); ap.add_argument("--Td", type=float)
    ap.add_argument("--ctrl-numz", type=float, nargs="+", dest="ctrl_numz")
    ap.add_argument("--ctrl-denz", type=float, nargs="+", dest="ctrl_denz")
    ap.add_argument("--input", type=str, choices=["step","ramp"], default="step")
    ap.add_argument("--ramp", action="store_true")
    ap.add_argument("--amp", type=float, default=1.0)
    ap.add_argument("--N", type=int, default=60)
    ap.add_argument("--cl-poles", type=str, nargs="+")
    ap.add_argument("--two-dof", action="store_true")
    ap.add_argument("--t-design", type=str, choices=["dc","lag","none","custom"], default="dc")
    ap.add_argument("--t-beta", type=float, default=0.85)
    ap.add_argument("--t-numz", type=float, nargs="+")
    ap.add_argument("--t-denz", type=float, nargs="+")
    ap.add_argument("--pre-numz", type=float, nargs="+")
    ap.add_argument("--pre-denz", type=float, nargs="+")
    ap.add_argument("--matplotlib", type=str)
    ap.add_argument("--csv", type=str)
    ap.add_argument("--pzmap", type=str)
    ap.add_argument("--rlocus", type=str)
    ap.add_argument("--plotly-step", type=str)
    ap.add_argument("--plotly-pz", type=str)
    ap.add_argument("--plotly-rl", type=str)
    ap.add_argument("--kmin", type=float, default=0.0); ap.add_argument("--kmax", type=float, default=20.0)
    ap.add_argument("--rlocus-log", action="store_true")
    ap.add_argument("--rclip", type=float, default=2.5)
    ap.add_argument("--pzclip", type=float, default=2.0)
    ap.add_argument("--panel", type=str)
    ap.add_argument("--outdir", type=str, default="out")
    ap.add_argument("--print-tf", action="store_true")

    args = ap.parse_args()
    if getattr(args, "ramp", False): args.input = "ramp"

    req = RunRequest(
        example37 = bool(args.example37),
        plant_num = args.plant_num, plant_den = args.plant_den, T = args.T,
        Kp = args.Kp, Ki = args.Ki, Kd = args.Kd,
        K = args.K, Ti = args.Ti, Td = args.Td,
        ctrl_numz = args.ctrl_numz, ctrl_denz = args.ctrl_denz,
        input = args.input, amp = args.amp, N = args.N,
        cl_poles = [complex(eval(s)) for s in args.cl_poles] if args.cl_poles else None,
        two_dof = bool(args.two_dof),
        t_design = args.t_design, t_beta = args.t_beta,
        t_numz = args.t_numz, t_denz = args.t_denz,
        pre_numz = args.pre_numz, pre_denz = args.pre_denz,
        matplotlib = args.matplotlib, csv = args.csv,
        pzmap = args.pzmap, rlocus = args.rlocus,
        plotly_step = args.plotly_step, plotly_pz = args.plotly_pz, plotly_rl = args.plotly_rl,
        kmin = args.kmin, kmax = args.kmax, rlocus_log = bool(args.rlocus_log),
        rclip = args.rclip, pzclip = args.pzclip,
        panel = args.panel, outdir = args.outdir, print_tf = bool(args.print_tf)
    )

    app = DiscreteResponseApp(req)
    app.run(
        matplotlib = req.matplotlib, csv = req.csv, pzmap = req.pzmap,
        rlocus = req.rlocus, plotly_step = req.plotly_step, plotly_pz = req.plotly_pz, plotly_rl = req.plotly_rl,
        panel = req.panel, outdir = req.outdir
    )

if __name__ == "__main__":
    main()
