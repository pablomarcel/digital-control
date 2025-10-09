#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse, os, sys

# ---------- Import shim so `python cli.py` works with absolute imports ----------
if __package__ in (None, ""):
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    from polePlacement.poleTool.apis import RunRequest
    from polePlacement.poleTool.app import PolePlacementApp
else:
    from .apis import RunRequest
    from .app import PolePlacementApp

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="digitalControl.polePlacement.poleTool — Discrete-time pole placement (Ogata §6-5)")
    ap.add_argument("--A", type=str)
    ap.add_argument("--B", type=str)
    ap.add_argument("--C", type=str)
    ap.add_argument("--json_in", type=str, help="Load A,B,C from JSON file with keys A,B,C")
    ap.add_argument("--poles", type=str, help='Desired poles, e.g. "0.5+0.5j,0.5-0.5j"')
    ap.add_argument("--deadbeat", action="store_true", help="Place all poles at 0 (SISO)")
    ap.add_argument("--method", type=str, default="auto",
                    choices=["auto", "ackermann", "ogata", "eigs", "place"])
    ap.add_argument("--plot", type=str, default="mpl", choices=["mpl", "plotly", "none"])
    ap.add_argument("--style", type=str, default="dots", choices=["dots", "stairs", "connected"])
    ap.add_argument("--samples", type=int, default=60)
    ap.add_argument("--pretty", action="store_true")
    ap.add_argument("--save_json", action="store_true")
    ap.add_argument("--save_csv", action="store_true")
    ap.add_argument("--name", type=str, default="pole_place")
    ap.add_argument("--outdir", type=str, help="Override output directory (default: package ./out)")
    return ap

def main(argv=None):
    ap = build_parser()
    ns = ap.parse_args(argv)

    req = RunRequest(
        A=ns.A, B=ns.B, C=ns.C,
        json_in=ns.json_in,
        poles=ns.poles,
        deadbeat=ns.deadbeat,
        method=ns.method,
        samples=ns.samples,
        plot=ns.plot,
        style=ns.style,
        pretty=ns.pretty,
        save_json=ns.save_json,
        save_csv=ns.save_csv,
        name=ns.name,
        outdir=ns.outdir,
    )
    app = PolePlacementApp()
    res = app.run(req)

    # Console summary (minimal; pretty printing can be added as needed)
    K = res["K"]; K0 = res["K0"]; eigs = res["Acl_eigs"]
    print("=== RESULTS ===")
    print("method:", res["resolved_method"])
    print("K:", K.ravel().tolist())
    print("K0:", K0.ravel().tolist())
    print("eig(A-BK):", eigs.tolist())
    print("placement error:", res["placement_error"])
    if res["plot_file"]: print("plot:", res["plot_file"])
    if res["csv_file"]: print("csv :", res["csv_file"])
    if res["json_file"]: print("json:", res["json_file"])

if __name__ == "__main__":
    main()
