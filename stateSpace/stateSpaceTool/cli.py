#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import os
import sys

# Import shim so "python cli.py" works with absolute imports
if __package__ in (None, ""):
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    from stateSpace.stateSpaceTool.apis import RunRequest
    from stateSpace.stateSpaceTool.app import StateSpaceApp
else:
    from .apis import RunRequest
    from .app import StateSpaceApp

def main():
    ap = argparse.ArgumentParser(description="stateSpace.stateSpaceTool - Canonical realizations (discrete SISO).")
    ap.add_argument("--num", type=str, default=None, help="Numerator per --form (coeffs or SymPy expr in z).")
    ap.add_argument("--den", type=str, default=None, help="Denominator per --form (coeffs or SymPy expr in z).")
    ap.add_argument("--form", type=str, default="auto", choices=["auto","zmin1","z","expr","zpk"])
    ap.add_argument("--zeros", type=str, default=None, help="ZPK zeros (space/comma).")
    ap.add_argument("--poles", type=str, default=None, help="ZPK poles (space/comma).")
    ap.add_argument("--gain", type=float, default=None, help="ZPK gain.")
    ap.add_argument("--forms", type=str, default="cont,obs,diag,jordan", help="Comma list subset of cont,obs,diag,jordan.")
    ap.add_argument("--realblocks", action="store_true", help="Make real 2x2 blocks for simple complex conj pairs.")
    ap.add_argument("--dt", type=float, default=1.0, help="Sample time for python-control checks.")
    ap.add_argument("--json-out", type=str, default=None, help="Write realizations JSON here.")
    ap.add_argument("--latex", action="store_true", help="Emit LaTeX blocks to stdout.")
    ap.add_argument("--latex-out", type=str, default=None, help="Write LaTeX blocks to file.")
    ap.add_argument("--check", type=str, default="brief", choices=["off","brief","full"], help="Roundtrip check verbosity.")
    ap.add_argument("--example", type=str, default=None, choices=["ogata_5_1"], help="Convenience textbook loader.")
    ap.add_argument("--quiet", action="store_true", help="Less console output.")
    args = ap.parse_args()

    if args.example == "ogata_5_1":
        args.num = "z + 1"
        args.den = "z**2 + 1.3*z + 0.4"
        args.form = "expr"

    req = RunRequest(
        form=args.form, num=args.num, den=args.den,
        zeros=args.zeros, poles=args.poles, gain=args.gain,
        forms=args.forms, realblocks=args.realblocks, dt=args.dt,
        latex=args.latex, latex_out=args.latex_out,
        json_out=args.json_out, check=args.check, quiet=args.quiet
    )
    app = StateSpaceApp()
    res = app.run(req)

    if not args.quiet:
        print("\n== Pulse transfer function ==")
        from stateSpace.stateSpaceTool.io import parse_poly
        from stateSpace.stateSpaceTool.design import pretty_tf_lines, pretty_ss_lines
        b, a = parse_poly(args.num, args.den, args.form, args.zeros, args.poles, args.gain)
        zm1, zdom = pretty_tf_lines(b, a)
        print("z^{-1} form  : H(z) =", zm1)
        print("z-domain form: H(z) =", zdom)

    from stateSpace.stateSpaceTool.design import pretty_ss_lines
    for key in ["cont","obs","diag","jordan"]:
        if key in res.realizations:
            import numpy as np
            def unjson(M):
                arr = []
                for row in M:
                    arr.append([c if isinstance(c,(int,float)) else complex(c[0], c[1]) for c in row])
                return np.array(arr, dtype=complex if any(isinstance(c, list) for r in M for c in r) else float)
            R = res.realizations[key]
            A,B,C,D = map(unjson, (R["A"], R["B"], R["C"], R["D"]))
            print(f"\n-- {key.capitalize()} --")
            x_line, y_line = pretty_ss_lines(A,B,C,D)
            print(x_line); print(y_line)

    if res.latex and args.latex:
        print("\n-- LaTeX --\n" + res.latex)

    if res.check_log and not args.quiet:
        print("\n" + res.check_log)

if __name__ == "__main__":
    main()
