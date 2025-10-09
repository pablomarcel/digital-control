
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import os
import sys
import numpy as np

# ---------- Import shim so `python cli.py` works with absolute imports ----------
if __package__ in (None, ""):
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    from polePlacement.transformationTool.apis import RunRequest
    from polePlacement.transformationTool.app import TransformationApp
    from polePlacement.transformationTool.io import parse_matrix, load_from_json
else:
    from .apis import RunRequest
    from .app import TransformationApp
    from .io import parse_matrix, load_from_json

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="polePlacement.transformationTool",
        description="Canonical-form transformations (Ogata §6-4). Run from inside the package.")
    g_in = p.add_mutually_exclusive_group(required=True)
    g_in.add_argument("--json", type=str, help="Path to in/<file>.json containing A,B,C,D")
    g_in.add_argument("--A", type=str, help='Matrix, e.g. "0 1; -2 -3"')

    p.add_argument("--B", type=str, default=None, help='Matrix, e.g. "0; 1" (n×1 for SISO)')
    p.add_argument("--C", type=str, default=None, help='Matrix, e.g. "1 0" (1×n for SISO)')
    p.add_argument("--D", type=str, default=None, help='Matrix, e.g. "0"')

    p.add_argument("--name", type=str, default="transform", help="Base name for outputs under out/")
    p.add_argument("--pretty", action="store_true", help="Pretty-print matrices")
    p.add_argument("--save-json", action="store_true", help="Save transformed system(s) to out/<name>_*.json")
    p.add_argument("--save-csv", action="store_true", help="Save transformed matrices as CSV")

    p.add_argument("--to-ccf", action="store_true", help="Controllable canonical form (SISO)")
    p.add_argument("--to-ocf", action="store_true", help="Observable canonical form (SISO)")
    p.add_argument("--to-diag", action="store_true", help="Diagonal canonical form (distinct eigenvalues)")
    p.add_argument("--to-jordan", action="store_true", help="Jordan form (symbolic via SymPy)")

    p.add_argument("--check-invariance", action="store_true", help="Show ctrb/obsv rank invariance after transform")
    p.add_argument("--show-tf", action="store_true", help="For SISO, print numerator/denominator coefficients (b,a)")

    return p

def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    # Load system
    if args.json:
        A, B, C, D = load_from_json(args.json)
    else:
        A = parse_matrix(args.A)
        B = parse_matrix(args.B) if args.B else None
        C = parse_matrix(args.C) if args.C else None
        D = parse_matrix(args.D) if args.D else None
        if B is not None and B.ndim == 1: B = B.reshape(-1, 1)
        if C is not None and C.ndim == 1: C = C.reshape(1, -1)
        if D is not None and D.ndim == 0: D = D.reshape(1, 1)

    req = RunRequest(
        A=A, B=B, C=C, D=D, json_in=args.json,
        to_ccf=args.to_ccf, to_ocf=args.to_ocf, to_diag=args.to_diag, to_jordan=args.to_jordan,
        show_tf=args.show_tf, check_invariance=args.check_invariance, pretty=args.pretty,
        name=args.name, save_json=args.save_json, save_csv=args.save_csv
    )

    app = TransformationApp()
    app.run(req)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
