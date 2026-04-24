
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse, os, sys

# ---------- Import shim so `python cli.py` works with absolute imports ----------
if __package__ in (None, ""):
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    from pole_placement.observabilityTool.apis import RunRequest
    from pole_placement.observabilityTool.app import ObservabilityApp
else:
    from .apis import RunRequest
    from .app import ObservabilityApp

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="digitalControl.pole_placement.observabilityTool — Ogata-grade observability toolbox")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--json", type=str, help="Path to JSON system file (expects keys A,C[,discrete])")
    src.add_argument("--A", type=str, help='A matrix string, e.g. "0 1; -2 -3"')

    p.add_argument("--C", type=str, help='C matrix string, e.g. "1 0" (required if not using --json).')
    p.add_argument("--discrete", action="store_true", help="Treat system as discrete-time.")
    p.add_argument("--horizon", type=int, default=None, help="Observability horizon (default n).")
    p.add_argument("--tol", type=float, default=None, help="Numeric rank tolerance (SVD).")

    # Tests
    p.add_argument("--pbh", action="store_true", help="Run PBH dual test for observability.")
    p.add_argument("--gram", action="store_true", help="Infinite-horizon observability Gramian (only if stable).")
    p.add_argument("--finite-dt", type=int, default=None, help="Finite-horizon DT observability Gramian over N steps.")
    p.add_argument("--finite-ct", type=float, default=None, help="Finite-horizon CT observability Gramian over time T seconds.")
    p.add_argument("--minreal", action="store_true", help="Trim unobservable modes and write *_minreal.json.")
    p.add_argument("--symbolic", action="store_true", help="SymPy exact rank of the observability matrix.")

    # Files / printing
    p.add_argument("--pretty", action="store_true", help="Pretty print matrices and results.")
    p.add_argument("--name", type=str, default="obsv", help="Base name for output files.")
    p.add_argument("--save-csv", action="store_true", help="Save observability matrix CSV to out/.")
    p.add_argument("--save-gram", action="store_true", help="Save any computed Gramian (infinite or finite) to CSV.")
    p.add_argument("--save-json", action="store_true", help="Save JSON summary to out/.")
    p.add_argument("--report", type=str, default=None, help="Optional text report path (e.g., out/obsv_report.txt).")
    return p

def main():
    ns = build_arg_parser().parse_args()
    req = RunRequest(
        json_in=ns.json,
        A=ns.A,
        C=ns.C,
        discrete=ns.discrete,
        horizon=ns.horizon,
        tol=ns.tol,
        do_pbh=ns.pbh,
        do_gram=ns.gram,
        finite_dt=ns.finite_dt,
        finite_ct=ns.finite_ct,
        do_minreal=ns.minreal,
        symbolic=ns.symbolic,
        pretty=ns.pretty,
        name=ns.name,
        save_csv=ns.save_csv,
        save_gram=ns.save_gram,
        save_json=ns.save_json,
        report=ns.report,
    )
    app = ObservabilityApp()
    res = app.run(req)
    if res.stdout:
        print(res.stdout)
    raise SystemExit(res.exit_code)

if __name__ == "__main__":
    main()
