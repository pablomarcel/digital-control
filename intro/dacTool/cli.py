#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse, os, sys

# ---------- Import shim so `python cli.py` works with absolute imports ----------
if __package__ in (None, ""):
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    from intro.dacTool.apis import RunRequest
    from intro.dacTool.app import run as run_app
else:
    from .apis import RunRequest
    from .app import run as run_app

def add_common(ap: argparse.ArgumentParser) -> None:
    ap.add_argument('--nbits', type=int, default=10)
    ap.add_argument('--vref', type=float, default=3.3)
    ap.add_argument('--csv', help="CSV with 'code' or per-bit b0..b{n-1}")
    ap.add_argument('--json', dest="jspec", help="JSON (inline or path): list of codes or per-bit dicts")
    ap.add_argument('--tupd', type=float, default=1e-6)
    ap.add_argument('--in-dir', default='in')
    ap.add_argument('--out-dir', default='out')
    ap.add_argument('--out', dest="out_csv", help='results CSV')
    ap.add_argument('--trace', dest="out_vcd", help='VCD path')
    ap.add_argument('--trace-all', dest="out_vcd_all", help='VCD aggregate path')
    ap.add_argument('--vcd-ideal', action='store_true', dest="include_ideal_in_vcd")
    ap.add_argument('--radix', choices=['dec','hex','bin','all'], default='dec')

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog='intro.dacTool', description='DAC simulator: R-2R and weighted-resistor')
    sub = ap.add_subparsers(dest='mode', required=True)

    r2r = sub.add_parser('r2r', help='R-2R ladder DAC')
    add_common(r2r)
    r2r.add_argument('--R', type=float, default=10_000.0, dest="R_ohm")
    r2r.add_argument('--sigma-r-pct', type=float, default=0.0)
    r2r.add_argument('--sigma-2r-pct', type=float, default=0.0)

    w = sub.add_parser('weighted', help='Binary weighted-resistor DAC')
    add_common(w)
    w.add_argument('--gain', type=float, default=1.0, dest="ro_over_r")
    w.add_argument('--res-sigma-pct', type=float, default=0.0)

    # Common analog path errors
    for p in (r2r, w):
        p.add_argument('--gain-err', type=float, default=0.0)
        p.add_argument('--vo-offset', type=float, default=0.0)

    return ap

def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    ns = ap.parse_args(argv)

    if ns.mode == 'r2r':
        req = RunRequest(
            dac_type='r2r',
            nbits=ns.nbits, vref=ns.vref,
            R_ohm=ns.R_ohm, sigma_r_pct=ns.sigma_r_pct, sigma_2r_pct=ns.sigma_2r_pct,
            gain_err=ns.gain_err, vo_offset=ns.vo_offset,
            csv=ns.csv, jspec=ns.jspec,
            tupd=ns.tupd, in_dir=ns.in_dir, out_dir=ns.out_dir,
            out_csv=ns.out_csv, out_vcd=ns.out_vcd, out_vcd_all=ns.out_vcd_all,
            include_ideal_in_vcd=ns.include_ideal_in_vcd, radix=ns.radix
        )
    else:
        req = RunRequest(
            dac_type='weighted',
            nbits=ns.nbits, vref=ns.vref,
            ro_over_r=ns.ro_over_r, res_sigma_pct=ns.res_sigma_pct,
            gain_err=ns.gain_err, vo_offset=ns.vo_offset,
            csv=ns.csv, jspec=ns.jspec,
            tupd=ns.tupd, in_dir=ns.in_dir, out_dir=ns.out_dir,
            out_csv=ns.out_csv, out_vcd=ns.out_vcd, out_vcd_all=ns.out_vcd_all,
            include_ideal_in_vcd=ns.include_ideal_in_vcd, radix=ns.radix
        )

    res = run_app(req)
    for m in res.messages:
        print(m)
    # Friendly stream log of each line
    for i, r in enumerate(res.rows):
        code = r.meta.get('code')
        vo_i = r.meta.get('vo_ideal')
        vo_n = r.meta.get('vo_nonideal')
        dv   = r.meta.get('error')
        print(f"[{i}] code={code} -> Vo_ideal={vo_i:.6g} V, Vo={vo_n:.6g} V, Δ={dv:+.6g} V")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
