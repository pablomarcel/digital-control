#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import os
import sys
import sympy as sp

# ---------- Import shim so `python cli.py` works with absolute imports ----------
if __package__ in (None, ""):
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    from stateSpace.liapunovTool.apis import RunRequest
    from stateSpace.liapunovTool.app import LyapunovApp
    from stateSpace.liapunovTool.design import fmt
else:
    from .apis import RunRequest
    from .app import LyapunovApp
    from .design import fmt

def main():
    ap = argparse.ArgumentParser(description="stateSpace.liapunovTool — Continuous/Discrete Lyapunov (Ogata §5-6)")
    sub = ap.add_subparsers(dest="cmd")

    ct = sub.add_parser("ct", help="Solve A^T P + P A = -Q (or A^* with --hermitian).")
    ct.add_argument("--A", required=True, help="System matrix A, e.g., '[[0 1]; [-25 -4]]'.")
    ct.add_argument("--Q", required=True, help="Weight matrix Q, e.g., '[[1 0]; [0 1]]'.")
    ct.add_argument("--hermitian", action="store_true", help="Use Hermitian A^* and enforce Hermitian P.")
    ct.add_argument("--digits", type=int, default=6)
    ct.add_argument("--evalf", type=int, default=None)
    ct.add_argument("--latex", action="store_true")
    ct.add_argument("--latex-out")
    ct.set_defaults(which=None)

    dt = sub.add_parser("dt", help="Solve G^T P G - P = -Q (or G^* with --hermitian).")
    dt.add_argument("--G", required=True, help="State matrix G, e.g., '[[0.97 0.05]; [-1.1 0.79]]'.")
    dt.add_argument("--Q", required=True, help="Weight matrix Q, e.g., '[[1 0]; [0 1]]'.")
    dt.add_argument("--hermitian", action="store_true", help="Use Hermitian G^* and enforce Hermitian P.")
    dt.add_argument("--digits", type=int, default=6)
    dt.add_argument("--evalf", type=int, default=None)
    dt.add_argument("--latex", action="store_true")
    dt.add_argument("--latex-out")
    dt.set_defaults(which=None)

    ex = sub.add_parser("example", help="Run built-in textbook examples (Ogata).")
    ex.add_argument("which", choices=["ogata_5_8", "ogata_5_9"])
    ex.add_argument("--digits", type=int, default=6)
    ex.add_argument("--evalf", type=int, default=None)
    ex.add_argument("--latex", action="store_true")
    ex.add_argument("--latex-out")

    args = ap.parse_args()
    if not args.cmd:
        ap.print_help()
        sys.exit(2)

    mode = "example" if args.cmd == "example" else args.cmd  # type: ignore
    req = RunRequest(
        mode=mode, A=getattr(args, "A", None), G=getattr(args, "G", None), Q=getattr(args, "Q", None),
        hermitian=getattr(args, "hermitian", False), digits=args.digits, evalf=args.evalf,
        latex=args.latex, latex_out=args.latex_out, which=getattr(args, "which", None)
    )

    app = LyapunovApp()
    res = app.run(req)

    print("\n== Results ==")
    print(f"mode = {res.mode}; hermitian = {res.hermitian}")
    print(f"P = {fmt(res.P)}")
    try:
        print(f"P (numeric) = {fmt(sp.N(res.P, args.digits))}")
    except Exception:
        pass
    print(f"definiteness: {res.pd_class}")
    if res.latex_text:
        print("\n== LaTeX ==")
        print(res.latex_text)

if __name__ == "__main__":
    main()
