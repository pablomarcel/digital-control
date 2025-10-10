#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import os
import sys
from typing import Optional

# ---------- Import shim so `python cli.py` works with absolute imports ----------
if __package__ in (None, ""):
    # Running as a script: add project root to sys.path and import absolute modules
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    from intro.zohTool.apis import RunRequest
    from intro.zohTool.app import ZOHApp
else:
    # Normal package execution
    from .apis import RunRequest
    from .app import ZOHApp

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description='intro.zohTool — Zero-Order Hold (ZOH) simulator')
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument('--csv',  help="input CSV with column 'u' (and optional 'k')")
    src.add_argument('--json', dest='json_spec', help="input JSON: list of numbers, list of {'u':..}, or {'vectors':[...]}" )

    ap.add_argument('--Ts', type=float, default=1e-3, help='sample period (seconds)')
    ap.add_argument('--delay', type=float, default=0.0, help='transport delay from sample to hold start (seconds)')
    ap.add_argument('--droop-tau', type=float, default=float('inf'),
                    help='hold droop time constant τ (seconds); use inf for ideal ZOH')
    ap.add_argument('--offset', type=float, default=0.0, help='constant offset added to the held value')

    ap.add_argument('--units', default='V', help='units string for logs/CSV (e.g., V, A, N)')
    ap.add_argument('--scale', type=float, default=1e6,
                    help='scale for VCD integer output (default: 1e6 for micro-units)')
    ap.add_argument('--idx-bits', type=int, default=None, help='optional bit-width for the VCD index signal')

    # Directories
    ap.add_argument('--in-dir',  default='in',  help='default input directory for relative filenames (default: in)')
    ap.add_argument('--out-dir', default='out', help='default output directory for relative filenames (default: out)')

    # Optional outputs
    ap.add_argument('--out',   dest='out_csv', help='optional results CSV')
    ap.add_argument('--trace', dest='out_vcd', help='optional VCD file (e.g., zoh.vcd)')
    return ap

def main(argv: Optional[list[str]] = None) -> int:
    ap = build_parser()
    ns = ap.parse_args(argv)

    req = RunRequest(
        csv=ns.csv,
        json_spec=ns.json_spec,
        Ts=ns.Ts,
        delay=ns.delay,
        droop_tau=ns.droop_tau,
        offset=ns.offset,
        units=ns.units,
        scale=ns.scale,
        idx_bits=ns.idx_bits,
        in_dir=ns.in_dir,
        out_dir=ns.out_dir,
        out_csv=ns.out_csv,
        out_vcd=ns.out_vcd,
    )
    app = ZOHApp()
    res = app.run(req)

    print(f"ZOH with Ts={ns.Ts:g} s, delay={ns.delay:g} s, droop_tau={ns.droop_tau}, offset={ns.offset} {ns.units}")
    for ev in res.events:
        print(f"[{ev.k}] t∈[{ev.t0:.6g},{ev.t1:.6g})  u={ev.u_in:.6g} {ns.units}  y0={ev.y0:.6g}  y1={ev.y1:.6g}")

    for m in res.messages:
        print(m)

    return 0

if __name__ == '__main__':
    raise SystemExit(main())
