#!/usr/bin/env python3
from __future__ import annotations
import argparse, os, sys, json

# ---------- Import shim so `python cli.py` works with absolute imports ----------
if __package__ in (None, ""):
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    from introduction.demuxTool.apis import RunRequest
    from introduction.demuxTool.app import DemuxApp
else:
    from .apis import RunRequest
    from .app import DemuxApp

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="introduction.demuxTool — N-way demultiplexer (PyRTL)")
    ap.add_argument('--csv',  help='input CSV with columns: sel,x')
    ap.add_argument('--json', help='input JSON (file or inline) or {"vectors":[...]}')
    ap.add_argument('--out',  help='optional CSV to write outputs')
    ap.add_argument('--n',    type=int, default=4, help='number of outputs (default 4)')
    ap.add_argument('--bits', type=int, default=8, help='data bitwidth (default 8)')
    ap.add_argument('--trace', help='optional VCD output filename (e.g., demux.vcd)')
    ap.add_argument('--strict', action='store_true', help='guard sel in [0..N-1] (invalid -> zeros)')
    # Directory policy
    ap.add_argument('--in-dir',  default='in',  help='default input directory for relative paths (default: in)')
    ap.add_argument('--out-dir', default='out', help='default output directory for relative paths (default: out)')
    return ap

def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    ns = ap.parse_args(argv)
    if not ns.csv and not ns.json:
        ap.error('provide --csv or --json')
    req = RunRequest(
        n_outputs=ns.n,
        data_bw=ns.bits,
        strict=ns.strict,
        csv_path=ns.csv,
        json_spec=ns.json,
        out_csv=ns.out,
        out_vcd=ns.trace,
        in_dir=ns.in_dir,
        out_dir=ns.out_dir,
    )
    app = DemuxApp()
    res = app.run(req)
    # Console echo similar to script: summarize rows
    for r in res.rows:
        outs = " ".join([f"y{k}={r[f'y{k}']}" for k in range(res.n_outputs)])
        print(f"[{r['cycle']}] sel={r['sel']} x={r['x']} => {outs}")
    if res.out_csv:
        print(f"Wrote results CSV to {res.out_csv}")
    if res.out_vcd:
        print(f"Wrote VCD wavefile to {res.out_vcd}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
