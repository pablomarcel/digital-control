#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import os
import sys

# ---------- Import shim so `python cli.py` works with absolute imports ----------
if __package__ in (None, ""):
    # Running as a script: add project root to sys.path and import absolute modules
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)

    from rst_controllers.rstTool.apis import RunRequest
    from rst_controllers.rstTool.app import RSTApp
    from rst_controllers.rstTool.io import parse_coeffs, parse_complex_list
    from rst_controllers.rstTool.design import poly_to_str, diff_eq_strings
else:
    # Normal package execution
    from .apis import RunRequest
    from .app import RSTApp
    from .io import parse_coeffs, parse_complex_list
    from .design import poly_to_str, diff_eq_strings


def main() -> None:
    p = argparse.ArgumentParser(
        prog="rst_controllers.rstTool",
        description="RST design & simulation (q=z^{-1}), outputs → rst_controllers/rstTool/out/",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # NOTE: --A and --B are OPTIONAL now to allow JSON-only runs
    p.add_argument("--A", help='A(q) coefficients (q=z^{-1}), e.g. "1 -0.8"')
    p.add_argument("--B", help='B(q) coefficients, e.g. "0.5"')
    p.add_argument("--d", type=int, default=0, help="Input delay ≥ 0")
    p.add_argument("--Ts", type=float, default=1.0, help="Sampling period for s→z mapping")

    # Target
    g = p.add_mutually_exclusive_group(required=False)
    g.add_argument("--Acl", help="Target A_cl(q) coefficients directly")
    g.add_argument("--poles", help='Target z-plane poles (space/comma separated), e.g. "0.6 0.6"')
    g.add_argument("--spoles", help='Target s-plane poles; mapped with z=exp(s*Ts), e.g. "-3+4j -3-4j"')
    p.add_argument("--Ac", help="Ac(q) coefficients")
    p.add_argument("--Ao", help="Ao(q) coefficients")

    # Degrees / policy
    p.add_argument("--degS", type=int, help="Degree of S(q) (override auto)")
    p.add_argument("--degR", type=int, help="Degree of R(q) (override auto)")
    p.add_argument("--alloc", choices=["S", "R"], default="S", help="Where to allocate extra degree")
    p.add_argument("--integrator", action="store_true", help="Include (1 - q) in S path")

    # Prefilter
    p.add_argument("--Tmode", choices=["unity_dc", "ac", "manual"], default="unity_dc", help="T selection mode")
    p.add_argument("--T", help="Manual T(q) if --Tmode=manual")

    # Simulation
    p.add_argument("--step", type=int, default=200, help="Sim length N (samples)")
    p.add_argument("--r_step", type=float, default=1.0, help="Reference step amplitude")
    p.add_argument("--v_step", type=float, default=0.0, help="Output disturbance step amplitude")
    p.add_argument("--v_k0", type=int, default=0, help="Disturbance step start index k0")
    p.add_argument("--noise", type=float, default=0.0, help="Measurement noise sigma")

    # I/O
    p.add_argument("--in_json", help="Load spec JSON (looked up under rst_controllers/rstTool/in by default)")
    p.add_argument("--export_json", nargs="?", const="rst_design.json", help="Export design pack JSON to out/<name>")
    p.add_argument("--save_csv", nargs="?", const="rst.csv", help="Save CSV (k,r,y,u,v) to out/<name>")

    p.add_argument("--pretty", action="store_true", help="Pretty console output")

    a = p.parse_args()

    # Build request. If A/B are omitted, app will try to pull from in_json.
    req = RunRequest(
        A=(parse_coeffs(a.A).tolist() if a.A else None),
        B=(parse_coeffs(a.B).tolist() if a.B else None),
        d=int(a.d),
        Ts=float(a.Ts),
        Acl=(parse_coeffs(a.Acl).tolist() if a.Acl else None),
        poles=(parse_complex_list(a.poles) if a.poles else None),
        spoles=(parse_complex_list(a.spoles) if a.spoles else None),
        Ac=(parse_coeffs(a.Ac).tolist() if a.Ac else None),
        Ao=(parse_coeffs(a.Ao).tolist() if a.Ao else None),
        degS=(int(a.degS) if a.degS is not None else None),
        degR=(int(a.degR) if a.degR is not None else None),
        alloc=a.alloc,
        integrator=bool(a.integrator),
        Tmode=a.Tmode,
        T=(parse_coeffs(a.T).tolist() if (a.Tmode == "manual" and a.T) else None),
        N=int(a.step),
        r_step=float(a.r_step),
        v_step=float(a.v_step),
        v_k0=int(a.v_k0),
        noise_sigma=float(a.noise),
        in_json=a.in_json,
        export_json=(a.export_json if a.export_json else None),
        save_csv=(a.save_csv if a.save_csv else None),
        pretty=bool(a.pretty),
    )

    app = RSTApp()
    res = app.run(req)

    if a.pretty:
        import numpy as np

        print("\n== Controller (RST) ==")
        print(f"S(q) = {poly_to_str(res.S)}")
        print(f"R(q) = {poly_to_str(res.R)}")
        print(f"T(q) = {poly_to_str(res.Tq)}  [mode={a.Tmode}, alloc={a.alloc}]")
        ctrl, ueq = diff_eq_strings(np.array(res.R), np.array(res.S), np.array(res.Tq))
        print("\n-- Control law --")
        print(ctrl)
        print(ueq)
        print(f"\nSSE: {res.sse:.6g}, y_final={res.y_final:.6g}, u_final={res.u_final:.6g}")
        if res.csv_path:
            print(f"Saved CSV: {res.csv_path}")
        if res.json_path:
            print(f"Exported JSON: {res.json_path}")


if __name__ == "__main__":
    main()
