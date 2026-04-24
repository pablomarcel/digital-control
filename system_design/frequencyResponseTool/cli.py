#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import os
import sys
import json

# ---------- Import shim so `python cli.py` works with absolute imports ----------
if __package__ in (None, ""):
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)

    from system_design.frequencyResponseTool.apis import RunRequest, LeadParams, LagParams, LagLeadParams
    from system_design.frequencyResponseTool.app import FrequencyResponseApp
    from system_design.frequencyResponseTool.io import parse_desc_list, write_manifest
else:
    from .apis import RunRequest, LeadParams, LagParams, LagLeadParams
    from .app import FrequencyResponseApp
    from .io import parse_desc_list, write_manifest

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="w-plane frequency-response design (lead/lag/lag-lead).")
    ap.add_argument("--T", type=float, required=True)
    ap.add_argument("--gz-num", type=str, required=True, help="G(z) numerator, descending z powers")
    ap.add_argument("--gz-den", type=str, required=True, help="G(z) denominator, descending z powers")
    ap.add_argument("--comp", choices=["none","lead","lag","laglead","auto"], default="none")

    # manual params
    ap.add_argument("--K", type=float, default=1.0)
    ap.add_argument("--alpha", type=float, default=0.4)
    ap.add_argument("--tau", type=float, default=0.5)
    ap.add_argument("--beta", type=float, default=4.0)
    ap.add_argument("--tau-lag", type=float, default=0.8)
    ap.add_argument("--tau-lead", type=float, default=0.2)

    # auto specs
    ap.add_argument("--pm", type=float, default=50.0)
    ap.add_argument("--gm", type=float, default=10.0)
    ap.add_argument("--Kv", type=float, default=2.0)

    # plotting
    ap.add_argument("--plot", action="append", choices=["matplotlib","plotly"])
    ap.add_argument("--save-mpl", action="store_true")
    ap.add_argument("--plotly-output", choices=["html","png","svg","pdf"], default="html")

    # step response
    ap.add_argument("--step", type=int, default=0)

    ap.add_argument("--out", type=str, default="out")
    return ap

def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)

    gz_num = parse_desc_list(args.gz_num)
    gz_den = parse_desc_list(args.gz_den)

    mode = args.comp
    lead = lag = laglead = None
    if mode == "lead":
        lead = LeadParams(K=args.K, alpha=args.alpha, tau=args.tau)
    elif mode == "lag":
        lag = LagParams(K=args.K, beta=args.beta, tau=args.tau)
    elif mode == "laglead":
        laglead = LagLeadParams(K=args.K, beta=args.beta, tau_lag=args.tau_lag, alpha=args.alpha, tau_lead=args.tau_lead)

    req = RunRequest(
        T=float(args.T),
        gz_num_desc=gz_num,
        gz_den_desc=gz_den,
        mode=mode,
        lead=lead, lag=lag, laglead=laglead,
        pm_req=float(args.pm), gm_req=float(args.gm), Kv_req=float(args.Kv),
        use_mpl=("matplotlib" in (args.plot or [])),
        save_mpl=bool(args.save_mpl),
        use_plotly=("plotly" in (args.plot or [])),
        plotly_fmt=str(args.plotly_output),
        step_N=int(args.step),
        out_dir=str(args.out)
    )

    app = FrequencyResponseApp()
    res = app.run(req)

    manifest = {
        "Gz_num_desc": gz_num,
        "Gz_den_desc": gz_den,
        "Gd_w_num_asc": res.Gd_w_num_asc,
        "Gd_w_den_asc": res.Gd_w_den_asc,
        "Gd_z_num_desc": res.Gd_z_num_desc,
        "Gd_z_den_desc": res.Gd_z_den_desc,
        "L_num_desc": res.L_num_desc,
        "L_den_desc": res.L_den_desc,
        "CL_num_desc": res.CL_num_desc,
        "CL_den_desc": res.CL_den_desc,
        "margins": {
            "nu_gc": res.margins.nu_gc,
            "nu_pc": res.margins.nu_pc,
            "pm_deg": res.margins.pm_deg,
            "gm_db": res.margins.gm_db
        },
        "files": [{"path": f.path, "desc": f.desc} for f in res.files]
    }
    path = write_manifest(args.out, manifest)

    print("\n=== Files generated in this run ===")
    for f in res.files + []:
        try:
            print(f"{f.path}  —  {f.desc}  ({os.path.getsize(f.path)} bytes)")
        except Exception:
            print(f"{f.path}  —  {f.desc}")
    print(f"{path}  —  Run manifest (JSON)")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
