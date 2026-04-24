#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, os, sys

# ---------- Import shim so `python cli.py` works with absolute imports ----------
if __package__ in (None, ""):
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    from introduction.vcdTool.apis import RunRequest
    from introduction.vcdTool.app import VCDApp
else:
    from .apis import RunRequest
    from .app import VCDApp

def parse_decode_list(s: str | None):
    out = []
    if not s: return out
    for item in s.split(','):
        item = item.strip()
        if not item: continue
        if ':' not in item:
            print(f"[warn] ignoring decode '{item}' (use name:nbits)", file=sys.stderr)
            continue
        name, n = item.split(':', 1)
        try:
            nbits = int(n); assert nbits > 0
        except Exception:
            print(f"[warn] ignoring decode '{item}' (nbits must be positive int)", file=sys.stderr)
            continue
        out.append((name, nbits))
    return out

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="introduction.vcdTool", description="Plot VCD signals with Matplotlib or Plotly")
    ap.add_argument('vcd', help='input VCD file (relative to --in-dir by default)')
    ap.add_argument('--signals', help='comma-separated signal names to plot (default: first 8)')
    ap.add_argument('--units', choices=['s','ms','us','ns'], default='us', help='x-axis units (default: us)')
    ap.add_argument('--backend', choices=['mpl','plotly'], default='mpl', help='which plot backend to use (default: mpl)')
    ap.add_argument('--overlay', action='store_true', help='(plotly) overlay signals on one axis instead of stacked subplots')
    ap.add_argument('--out-csv', dest='out_csv', help='optional CSV export of the traces')
    ap.add_argument('--csv-units', choices=['s','ms','us','ns'], default='s', help='time units for CSV (default: s)')
    ap.add_argument('--png', help='save Matplotlib figure to PNG (mpl backend)')
    ap.add_argument('--html', help='save Plotly figure to HTML (plotly backend)')
    ap.add_argument('--decode', help="split buses into bits, e.g. --decode 'code:10,bus:8'")
    ap.add_argument('--in-dir',  default='in',  help="default input directory for relative VCD (default: in)")
    ap.add_argument('--out-dir', default='out', help="default output directory for relative files (default: out)")
    return ap

def main(argv=None):
    ap = build_parser()
    ns = ap.parse_args(argv)

    req = RunRequest(
        vcd=ns.vcd,
        signals=[s.strip() for s in ns.signals.split(',')] if ns.signals else None,
        units=ns.units,
        backend=ns.backend,
        overlay=ns.overlay,
        out_csv=ns.out_csv,
        csv_units=ns.csv_units,
        png=ns.png,
        html=ns.html,
        decode=parse_decode_list(ns.decode),
        in_dir=ns.in_dir,
        out_dir=ns.out_dir,
    )

    app = VCDApp()
    res = app.run(req)
    # Pretty print a short manifest-like summary
    print("\n=== vcdTool manifest ===")
    print(f"VCD: {res['vcd']}")
    print(f"Signals: {', '.join(res['signals'])}")
    outs = res['out']
    print(f"PNG:  {outs.get('png')}")
    print(f"HTML: {outs.get('html')}")
    print(f"CSV:  {outs.get('csv')}\n")

if __name__ == '__main__':
    main()
