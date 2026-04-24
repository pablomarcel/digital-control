
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse, os, sys

# ---------- Import shim so `python cli.py` works with absolute imports ----------
if __package__ in (None, ""):
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    from introduction.muxTool.apis import RunRequest
    from introduction.muxTool.app import MuxApp
else:
    from .apis import RunRequest
    from .app import MuxApp

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="introduction.muxTool — 4:1 multiplexer (PyRTL)")
    ap.add_argument('--csv',  help='input CSV with columns: sel,d0,d1,d2,d3')
    ap.add_argument('--json', help='input JSON (file or inline): list or {"vectors":[...]} of {sel,d0,d1,d2,d3}')
    ap.add_argument('--out',  help='optional CSV to write outputs (relative -> out/<name>)')
    ap.add_argument('--bits', type=int, default=8, help='data bitwidth (default 8)')
    ap.add_argument('--trace', help='optional VCD output filename (relative -> out/<name>)')

    ap.add_argument('--in', dest='in_dir', default='in', help='default input directory for relative filenames (default: in)')
    ap.add_argument('--outdir', dest='out_dir', default='out', help='default output directory for relative filenames (default: out)')
    return ap

def main(argv=None) -> int:
    ap = build_parser()
    ns = ap.parse_args(argv)

    if not ns.csv and not ns.json:
        ap.error('provide --csv or --json')

    req = RunRequest(csv=ns.csv, json=ns.json, out=ns.out, bits=ns.bits, trace=ns.trace, in_dir=ns.in_dir, out_dir=ns.out_dir)
    app = MuxApp()
    res = app.run(req)

    # Minimal CLI output
    for r in res.rows:
        print(f"[{r['cycle']}] sel={r['sel']} d0={r['d0']} d1={r['d1']} d2={r['d2']} d3={r['d3']} => y={r['y']}")
    if res.out_csv:
        print(f"Wrote results CSV to {res.out_csv}")
    if res.out_vcd:
        print(f"Wrote VCD wavefile to {res.out_vcd}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
