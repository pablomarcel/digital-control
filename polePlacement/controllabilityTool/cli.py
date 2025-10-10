#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import os
import sys

# ---------- Import shim so `python cli.py` works with absolute imports ----------
if __package__ in (None, ""):
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    from polePlacement.controllabilityTool.apis import RunRequest
    from polePlacement.controllabilityTool.app import ControllabilityApp
else:
    from .apis import RunRequest
    from .app import ControllabilityApp

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="polePlacement.controllabilityTool",
        description="Ogata-grade controllability toolbox (CT/DT) — state & output controllability, PBH, Gramians, minreal."
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--json", type=str, help="Path to JSON system file (usually under in/).")
    src.add_argument("--A", type=str, help='A matrix string, e.g. "0 1; -2 -3"')

    p.add_argument("--B", type=str, help='B matrix string, e.g. "0; 1" (required if not using --json).')
    p.add_argument("--C", type=str, help='C matrix string, needed for --output-ctrb.')
    p.add_argument("--D", type=str, help='D matrix string (optional, for --output-ctrb).')

    p.add_argument("--discrete", action="store_true", help="Treat system as discrete-time.")
    p.add_argument("--horizon", type=int, default=None, help="Controllability/output horizon (default n).")
    p.add_argument("--tol", type=float, default=None, help="Numeric rank tolerance (SVD).")

    # State tests
    p.add_argument("--pbh", action="store_true", help="Run PBH controllability test.")
    p.add_argument("--gram", action="store_true", help="Infinite-horizon controllability Gramian (only if stable).")
    p.add_argument("--finite-dt", type=int, default=None, help="Finite-horizon DT Gramian over N steps.")
    p.add_argument("--finite-ct", type=float, default=None, help="Finite-horizon CT Gramian over time T seconds.")
    p.add_argument("--minreal", action="store_true", help="Trim uncontrollable modes and write *_minreal.json.")
    p.add_argument("--symbolic", action="store_true", help="SymPy exact rank of the controllability matrix.")

    # Output controllability
    p.add_argument("--output-ctrb", action="store_true", help="Run output controllability rank test (needs C, optional D).")
    p.add_argument("--save-output-csv", action="store_true", help="Save output controllability matrix to out/.")

    # Output files / printing
    p.add_argument("--pretty", action="store_true", help="Pretty print matrices and results.")
    p.add_argument("--name", type=str, default="ctrb", help="Base name for output files.")
    p.add_argument("--save-csv", action="store_true", help="Save controllability matrix CSV to out/.")
    p.add_argument("--save-json", action="store_true", help="Save JSON summary to out/.")
    p.add_argument("--save-gram", action="store_true", help="Save any computed Gramian (infinite or finite) to CSV.")
    p.add_argument("--report", type=str, default=None, help="Optional text report path (e.g., out/ctrb_report.txt).")
    return p

def main() -> int:
    ns = build_arg_parser().parse_args()
    req = RunRequest(
        json_path=ns.json,
        A=ns.A,
        B=ns.B,
        C=ns.C,
        D=ns.D,
        discrete=ns.discrete,
        horizon=ns.horizon,
        tol=ns.tol,
        pbh=ns.pbh,
        gram=ns.gram,
        finite_dt=ns.finite_dt,
        finite_ct=ns.finite_ct,
        minreal=ns.minreal,
        symbolic=ns.symbolic,
        output_ctrb=ns.output_ctrb,
        save_output_csv=ns.save_output_csv,
        pretty=ns.pretty,
        name=ns.name,
        save_csv=ns.save_csv,
        save_json=ns.save_json,
        save_gram=ns.save_gram,
        report=ns.report,
    )
    app = ControllabilityApp()
    res = app.run(req)
    return res.exit_code

if __name__ == "__main__":
    raise SystemExit(main())
