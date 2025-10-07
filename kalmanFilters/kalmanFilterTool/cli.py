#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI entry for the Kalman Filter tool

Works in two modes:
  1) From project root (preferred):  python -m kalmanFilters.kalmanFilterTool.cli --help
  2) From inside this folder:        python cli.py --help
     (import shim below handles absolute imports)

Default I/O when running *inside* kalmanFilterTool/:
  * Inputs : ./in
  * Outputs: ./out
"""
from __future__ import annotations

# ---------- Import shim so `python cli.py` works with absolute imports ----------
if __package__ in (None, ""):
    # Running as a script: add project root to sys.path and import absolute modules
    import os, sys
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    from kalmanFilters.kalmanFilterTool.apis import RunRequest
    from kalmanFilters.kalmanFilterTool.app import KalmanFilterApp
    from kalmanFilters.kalmanFilterTool.io import parse_matrix, parse_vector
else:
    # Normal package execution
    from .apis import RunRequest
    from .app import KalmanFilterApp
    from .io import parse_matrix, parse_vector

import argparse

_INSIDE_PACKAGE = (__package__ in (None, ""))

def _default_in_dir() -> str:
    return "in" if _INSIDE_PACKAGE else "kalmanFilters/kalmanFilterTool/in"

def _default_out_dir() -> str:
    return "out" if _INSIDE_PACKAGE else "kalmanFilters/kalmanFilterTool/out"

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="kalmanFilters.kalmanFilterTool" if not _INSIDE_PACKAGE else "kalmanFilterTool.cli",
        description="Discrete Kalman filter simulation (time-varying or steady-state) — OOP module",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        allow_abbrev=False,
    )
    # High-level CV defaults
    ap.add_argument("--dt", type=float, default=0.05, help="Sample time (s)")
    ap.add_argument("--T",  type=float, default=10.0, help="Simulation duration (s)")
    ap.add_argument("--q",  type=float, default=0.25, help="Accel noise intensity (CV model)")
    ap.add_argument("--r",  type=float, default=4.0,   help="Measurement noise variance (CV model)")
    ap.add_argument("--u",  type=float, default=0.0,   help="Constant input acceleration")
    # Overrides
    ap.add_argument("--A", help='Override A, e.g. "1 0.05; 0 1"')
    ap.add_argument("--B", help='Override B, e.g. "0.00125; 0.05"')
    ap.add_argument("--C", help='Override C, e.g. "1 0" or "1 0; 0 1"')
    ap.add_argument("--G", help='Override G, process noise input matrix (n×m)')
    ap.add_argument("--Q", help='Override Q: n×n (state-form) or m×m (input-form with G)')
    ap.add_argument("--R", help='Override R (p×p); scalar expands to p×p*scalar')
    # Initials
    ap.add_argument("--x0",  default="0 0", help='Initial state estimate x0 (column)')
    ap.add_argument("--P0",  default="100 0; 0 100", help='Initial covariance P0')
    ap.add_argument("--xtrue0", default="0 0", help='True initial state (for sim)')
    # Flags
    ap.add_argument("--steady", action="store_true", help="Use steady-state KF (DARE)")
    ap.add_argument("--seed", type=int, default=1, help="Random seed")
    ap.add_argument("--backend", choices=["mpl","plotly","both","none"], default="both", help="Plotting backend(s)")
    # Outputs
    ap.add_argument("--save_csv",  default=None, help="CSV filename")
    ap.add_argument("--save_png",  default=None, help="PNG filename (MPL)")
    ap.add_argument("--save_html", default=None, help="HTML filename (Plotly)")
    ap.add_argument("--no_show", action="store_true", help="Do not open plot windows (MPL)")
    # Directories
    ap.add_argument("--in-dir",  default=_default_in_dir(),  help="Default input directory")
    ap.add_argument("--out-dir", default=_default_out_dir(), help="Output directory for relative filenames")
    return ap

def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)
    req = RunRequest(
        dt=args.dt, T=args.T, q=args.q, r=args.r, u=args.u,
        steady=args.steady, seed=args.seed, backend=args.backend,
        A=(parse_matrix(args.A) if args.A is not None else None),
        B=(parse_matrix(args.B) if args.B is not None else None),
        C=(parse_matrix(args.C) if args.C is not None else None),
        G=(parse_matrix(args.G) if args.G is not None else None),
        Q=(parse_matrix(args.Q) if args.Q is not None else None),
        R=(parse_matrix(args.R) if args.R is not None else None),
        x0=parse_vector(args.x0),
        P0=parse_matrix(args.P0),
        xtrue0=parse_vector(args.xtrue0),
        save_csv=args.save_csv, save_png=args.save_png, save_html=args.save_html,
        no_show=args.no_show, in_dir=args.in_dir, out_dir=args.out_dir
    )
    KalmanFilterApp().build_and_run(req)

if __name__ == "__main__":
    main()
