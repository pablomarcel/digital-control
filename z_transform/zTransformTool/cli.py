#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
"""
cli.py — Entry point for zTransformTool.

Supports:
- python -m z_transform.zTransformTool.cli
- python z_transform/zTransformTool/cli.py  (import shim below)
"""
import argparse
import os
import sys

# ---------- Import shim so `python cli.py` works with absolute imports ----------
if __package__ in (None, ""):
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    from z_transform.zTransformTool.apis import RunRequest
    from z_transform.zTransformTool.app import ZTApp
else:
    from .apis import RunRequest
    from .app import ZTApp

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="zTransformTool — Object-oriented Z-transform workflows")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--z", action="store_true", help="Forward Z-transform from x(k)")
    g.add_argument("--zt", action="store_true", help="Forward Z-transform from x(t) sampled: x(k)=x(kT)")
    g.add_argument("--iz", action="store_true", help="Inverse Z-transform (unilateral)")
    g.add_argument("--series", action="store_true", help="Direct-division series in z^{-1}")
    g.add_argument("--residuez", action="store_true", help="SciPy residuez in z^{-1}")
    g.add_argument("--tf", action="store_true", help="Discrete TF utilities (python-control)")
    g.add_argument("--diff", action="store_true", help="Solve difference equation")

    # Common
    p.add_argument("--expr", type=str, help="x(k) for --z")
    p.add_argument("--xt", type=str, help="x(t) for --zt; samples x(k)=x(kT)")
    p.add_argument("--X", type=str, help="X(z) for --iz/--series")
    p.add_argument("--subs", type=str, help="Substitutions: 'T=0.1,w=2,a=0.3,b=0.7'")
    p.add_argument("--N", type=int, help="Sequence length / series order")
    p.add_argument("--latex", action="store_true", help="Print LaTeX instead of ASCII")
    p.add_argument("--pretty", action="store_true", help="(No-op) pretty by default")
    p.add_argument("--export_csv", type=str, help="CSV path for sequences (relative goes to package out/)")
    p.add_argument("--export_json", type=str, help="JSON path for sequences (relative goes to package out/)")

    # residuez / tf
    p.add_argument("--num", type=str, help="Numerator coeffs (z^{-1} powers)")
    p.add_argument("--den", type=str, help="Denominator coeffs (z^{-1} powers)")
    p.add_argument("--dt", type=float, default=1.0, help="Sampling period for TF (default 1)")
    p.add_argument("--impulse", action="store_true", help="Impulse response")
    p.add_argument("--step", action="store_true", help="Step response")
    p.add_argument("--u", type=str, help="Forced-response input sequence")

    # difference equations
    p.add_argument("--rec", type=str, help="Full recurrence, e.g. 'Eq(x(k+2)+3*x(k+1)+2*x(k), 0)'")
    p.add_argument("--a", type=str, help="LHS coeffs a0..an (symbolic allowed), e.g. '1 (a+b) a*b'")
    p.add_argument("--rhs", type=str, help="RHS in k (optional)")
    p.add_argument("--ics", type=str, help="Initial conditions: 'x0=0,x1=1'")

    return p

def main():
    parser = build_parser()
    args = parser.parse_args()

    mode = None
    if args.z: mode = "forward"
    elif args.zt: mode = "forward_xt"
    elif args.iz: mode = "inverse"
    elif args.series: mode = "series"
    elif args.residuez: mode = "residuez"
    elif args.tf: mode = "tf"
    elif args.diff: mode = "diff"

    req = RunRequest(
        mode=mode,
        expr=args.expr, xt=args.xt, X=args.X, subs=args.subs, N=args.N,
        latex=args.latex, export_csv=args.export_csv, export_json=args.export_json,
        num=args.num, den=args.den, dt=args.dt, impulse=args.impulse, step=args.step, u=args.u,
        rec=args.rec, a=args.a, rhs=args.rhs, ics=args.ics
    )
    app = ZTApp(print_boxes=True)
    app.run(req)

if __name__ == "__main__":
    main()
