
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, os, sys

# ---------- Import shim so `python cli.py` works with absolute imports ----------
if __package__ in (None, ""):
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    from intro.adcTool.apis import RunRequest
    from intro.adcTool.app import ADCApp
else:
    from .apis import RunRequest
    from .app import ADCApp

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="intro.adcTool — Counter & SAR ADC simulators")
    ap.add_argument('--type', dest='adc_type', choices=['counter','sar'], required=True, help='ADC type')
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument('--csv', help="CSV with column 'vin'")
    src.add_argument('--json', help="JSON file or inline JSON of VIN values")

    ap.add_argument('--nbits', type=int, default=10)
    ap.add_argument('--vref',  type=float, default=3.3)
    ap.add_argument('--comp-offset', type=float, default=0.0)
    ap.add_argument('--dac-gain',    type=float, default=1.0)
    ap.add_argument('--dac-offset',  type=float, default=0.0)
    ap.add_argument('--jitter-rms',  type=float, default=0.0)
    ap.add_argument('--radix', choices=['dec','hex','bin','all'], default='dec')

    # timing
    ap.add_argument('--tclk', type=float, default=1e-6, help='Counter ADC clock period')
    ap.add_argument('--tbit', type=float, default=1e-6, help='SAR ADC bit decision period')

    # dir policy
    ap.add_argument('--in-dir', default='in')
    ap.add_argument('--out-dir', default='out')

    # outputs
    ap.add_argument('--out', dest='out_csv', help='Results CSV')
    ap.add_argument('--trace', dest='trace_vcd', help='VCD for last conversion')
    ap.add_argument('--trace-all', dest='trace_all_vcd', help='VCD accumulating all conversions')
    return ap

def main(argv=None):
    ap = build_parser()
    ns = ap.parse_args(argv)

    req = RunRequest(
        adc_type=ns.adc_type, csv=ns.csv, json=ns.json,
        nbits=ns.nbits, vref=ns.vref,
        comp_offset=ns.comp_offset, dac_gain=ns.dac_gain, dac_offset=ns.dac_offset,
        jitter_rms=ns.jitter_rms, radix=ns.radix,
        tclk=ns.tclk, tbit=ns.tbit,
        in_dir=ns.in_dir, out_dir=ns.out_dir,
        out_csv=ns.out_csv, trace_vcd=ns.trace_vcd, trace_all_vcd=ns.trace_all_vcd,
    )
    app = ADCApp()
    app.run(req)

if __name__ == "__main__":
    main()
