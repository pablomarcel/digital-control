
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

    from systemDesign.juryTestTool.apis import RunRequest
    from systemDesign.juryTestTool.app import JuryTestApp
else:
    from .apis import RunRequest
    from .app import JuryTestApp

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="systemDesign.juryTestTool",
        description="Stability checker: Jury, Schur–Cohn, Bilinear–Routh (with K solving).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--coeffs", type=str,
                     help="Comma/space-separated a0..an (high→const). Example: '1, -1.2, 0.07, 0.3, -0.08'")
    src.add_argument("--json_in", type=str,
                     help="JSON in in/: { 'coeffs': [...], 'variable':'z', 'param':'K' }")

    p.add_argument("--method", choices=("jury","schur","bilinear","all"), default="jury",
                   help="Which method to run.")
    p.add_argument("--solve_range", action="store_true",
                   help="Solve inequalities for parameter range (if param present).")
    p.add_argument("--eval_K", type=float, default=None,
                   help="Evaluate stability at this K and print roots.")
    p.add_argument("--T", type=float, default=None,
                   help="Sampling period (s). If critical (|z|=1) and n=2, report ω_d = θ/T.")
    p.add_argument("--rational", action="store_true",
                   help="Parse decimals as exact rationals.")

    p.add_argument("--abs_tol", type=float, default=1e-10,
                   help="Absolute tolerance for boundary detection in inequalities.")
    p.add_argument("--rel_tol", type=float, default=1e-9,
                   help="Relative tolerance for boundary detection in inequalities.")
    p.add_argument("--unit_tol", type=float, default=2e-6,
                   help="Tolerance for |z|≈1 boundary via roots (default 2e-6).")

    p.add_argument("--save_table", type=str, default=None,
                   help="Save ASCII table(s) to out/ (Jury / Schur / Routh).")
    p.add_argument("--save_json", type=str, default=None,
                   help="Save JSON report to out/.")

    return p

def main(argv=None):
    args = build_parser().parse_args(argv)
    req = RunRequest(
        coeffs=args.coeffs,
        json_in=args.json_in,
        method=args.method, solve_range=args.solve_range,
        eval_K=args.eval_K, T=args.T, rational=args.rational,
        abs_tol=args.abs_tol, rel_tol=args.rel_tol, unit_tol=args.unit_tol,
        save_table=args.save_table, save_json=args.save_json
    )
    app = JuryTestApp()
    res = app.run(req)
    # Lightweight console summary
    print(f"\nP(z): {res.polynomial}")
    print(f"Order: {res.order}")
    for name, m in res.methods.items():
        print(f"[{name}] Verdict: {m.verdict}")
    if res.eval_summary:
        print("\n[Eval] K={K}, roots={roots}, radii={radii}, omega_d={omega_d}".format(**res.eval_summary or {}))

if __name__ == "__main__":
    main()
