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
    from state_space.stateConverterTool.apis import RunRequest
    from state_space.stateConverterTool.app import StateConverterApp
    from state_space.stateConverterTool.io import parse_matrix, parse_scalar
    from state_space.stateConverterTool.design import fmt
else:
    from .apis import RunRequest
    from .app import StateConverterApp
    from .io import parse_matrix, parse_scalar
    from .design import fmt

def main():
    ap = argparse.ArgumentParser(description="ZOH discretization and pulse transfer F(z) with tidy one-line printing.")
    ap.add_argument("--A"); ap.add_argument("--B"); ap.add_argument("--C"); ap.add_argument("--D"); ap.add_argument("--T")
    ap.add_argument("--digits", type=int, default=6, help="Digits for numeric printouts (default 6).")
    ap.add_argument("--evalf", type=int, default=None, help="Evaluate numeric inputs to floats with this many digits (fast path).")
    ap.add_argument("--no-simplify", action="store_true", help="Skip final symbolic simplify/together/cancel (faster).")
    ap.add_argument("--force-inverse", action="store_true", help="Also compute and print (zI-G)^{-1} explicitly.")
    ap.add_argument("--no-fallback", action="store_true", help="Disable augmented-expm fallback when A is singular.")
    ap.add_argument("--latex", action="store_true", help="Emit LaTeX blocks to stdout.")
    ap.add_argument("--latex-out", help="Write LaTeX to file (under ./out recommended).")
    ap.add_argument("--example", choices=["ogata_5_4","ogata_5_5","matlab_p318"], help="Run a built-in textbook example.")
    args = ap.parse_args()

    if args.example is None:
        missing = [k for k in ("A","B","C","D","T") if getattr(args,k) is None]
        if missing:
            ap.error("Missing required arguments: " + ", ".join(missing))

    req = RunRequest(
        A=parse_matrix(args.A) if args.A else None,
        B=parse_matrix(args.B) if args.B else None,
        C=parse_matrix(args.C) if args.C else None,
        D=parse_matrix(args.D) if args.D else None,
        T=parse_scalar(args.T) if args.T else None,
        example=args.example,
        digits=args.digits,
        evalf=args.evalf,
        simplify=not args.no_simplify,
        force_inverse=args.force_inverse,
        allow_singular_fallback=not args.no_fallback,
        want_latex=args.latex,
        latex_out=args.latex_out,
    )

    app = StateConverterApp()
    try:
        res = app.run(req)
    except RuntimeError as e:
        # Friendly error path (e.g., --no-fallback + singular A)
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)

    # Pretty printing (scalar vs matrix) kept simple
    print("\n== Discrete-time (ZOH) result ==")
    print("G(T) =", fmt(res.G))
    print("H(T) =", fmt(res.H))
    if res.Finv is not None:
        print("(zI - G)^(-1) =", fmt(res.Finv))
    # For SISO output, unwrap 1x1
    if res.F.shape == (1,1):
        print("F(z) =", fmt(res.F[0,0]))
    else:
        print("F(z) =", fmt(res.F))

    if res.latex and args.latex:
        print("\n== LaTeX ==")
        print(res.latex)

if __name__ == "__main__":
    main()
