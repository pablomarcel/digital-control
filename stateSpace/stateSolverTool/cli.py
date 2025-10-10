
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

    from stateSpace.stateSolverTool.apis import RunRequest
    from stateSpace.stateSolverTool.app import StateSolverApp
else:
    from .apis import RunRequest
    from .app import StateSolverApp

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="stateSpace.stateSolverTool — Symbolic State Solver (LTI/LTV)")
    ap.add_argument("--mode", choices=["lti", "ltv"], default="lti")
    ap.add_argument("--example", choices=["ogata_5_2", "ogata_5_3"], default=None)
    # LTI
    ap.add_argument("--G"); ap.add_argument("--H"); ap.add_argument("--C"); ap.add_argument("--D")
    ap.add_argument("--x0"); ap.add_argument("--u")
    # LTV
    ap.add_argument("--Gk"); ap.add_argument("--Hk"); ap.add_argument("--Ck"); ap.add_argument("--Dk")
    # Options
    ap.add_argument("--latex", action="store_true")
    ap.add_argument("--latex-out", type=str, default=None)
    ap.add_argument("--zt", action="store_true")
    ap.add_argument("--realblocks", action="store_true")
    ap.add_argument("--steps", type=int, default=6)
    ap.add_argument("--check", choices=["off", "brief"], default="brief")
    ap.add_argument("--power-style", choices=["rational", "integer"], default="rational")
    return ap

def main(argv=None):
    argv = argv or sys.argv[1:]
    ap = build_parser()
    ns = ap.parse_args(argv)

    # Locate package dir (for out/)
    if __package__ in (None, ""):
        pkg_dir = os.path.dirname(__file__)
    else:
        pkg_dir = os.path.dirname(__file__)

    app = StateSolverApp(pkg_dir=pkg_dir)
    req = RunRequest(
        mode=ns.mode, example=ns.example,
        G=ns.G, H=ns.H, C=ns.C, D=ns.D, x0=ns.x0, u=ns.u,
        Gk=ns.Gk, Hk=ns.Hk, Ck=ns.Ck, Dk=ns.Dk,
        latex=ns.latex, latex_out=ns.latex_out, zt=ns.zt,
        realblocks=ns.realblocks, steps=ns.steps, check=ns.check,
        power_style=ns.power_style
    )
    res = app.run(req)

    # Console reporting (succinct; rich info lives in res)
    import sympy as sp
    from stateSpace.stateSolverTool.io import fmt_matrix_for_console as fmt

    if res.mode == "lti":
        m = res.lti.matrices
        print("\n== LTI system ==")
        print("G = {}".format(fmt(m.G))); print("H = {}".format(fmt(m.H)))
        print("C = {}".format(fmt(m.C))); print("D = {}".format(fmt(m.D)))
        print("x(0) = {}".format(fmt(m.x0))); print("u(k) = {}".format(sp.sstr(m.u_expr)))
        print("\n(zI - G)^(-1) = {}".format(fmt(res.lti.inv_zI_minus_G)))
        print("Psi(k) = {}".format(fmt(res.lti.Psi)))
        print("x(k)   = {}".format(fmt(res.lti.xk)))
        print("y(k)   = {}".format(fmt(res.lti.yk)))
        if res.lti.check_status:
            print(f"[check] brief: {res.lti.check_status}")
        if res.lti.latex_lines and ns.latex_out:
            print(f"Saved LaTeX to {ns.latex_out if os.path.isabs(ns.latex_out) else os.path.join('out', ns.latex_out)}")
    else:
        print("\n== LTV system ==")
        print(f"[check] brief: {res.ltv.check_status}")
        print("Phi = {}".format(fmt(res.ltv.Phi)))
        for i, xi in enumerate(res.ltv.xs[: ns.steps+1]):
            print(f"x({i}) = {fmt(xi)}")
        for i, yi in enumerate(res.ltv.ys[: ns.steps]):
            yM = yi if isinstance(yi, sp.MatrixBase) else sp.Matrix([[yi]])
            print(f"y({i}) = {fmt(yM)}")

if __name__ == "__main__":
    main()
