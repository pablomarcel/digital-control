#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, os, sys, json

# Import shim so `python cli.py` works with absolute imports
if __package__ in (None, ''):
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    from polePlacement.servoTool.apis import RunRequest
    from polePlacement.servoTool.app import ServoApp
else:
    from .apis import RunRequest
    from .app import ServoApp

def build_parser():
    p = argparse.ArgumentParser(prog='polePlacement.servoTool', description='Servo-system design & simulation (Ogata Ch.6)')
    sub = p.add_subparsers(dest='cmd', required=True)

    def add_eq_opts(pp):
        pp.add_argument('--eq', action='store_true', help='Print one-liner equations.')
        pp.add_argument('--eq-stdout', action='store_true', help='Send equations to stdout (default: stderr).')
        pp.add_argument('--eq-file', type=str, default=None, help='Write equations to this file (overrides stdout/stderr).')

    s = sub.add_parser('example', help='Run Ogata Example 6-13 end-to-end')
    s.add_argument('--plot', action='store_true')
    s.add_argument('--plotly', action='store_true')
    s.add_argument('--html', type=str, default=None)
    s.add_argument('--open', action='store_true')
    s.add_argument('--savefig', type=str, default=None)
    add_eq_opts(s)

    s = sub.add_parser('design', help='Design K1, K2')
    s.add_argument('--config', type=str, default=None)
    s.add_argument('--G', type=str); s.add_argument('--H', type=str); s.add_argument('--C', type=str)
    s.add_argument('--which', type=str, choices=['ogata', 'aug'], default='ogata')
    s.add_argument('--method', type=str, choices=['acker', 'place', 'acker_ct'], default='acker')
    s.add_argument('--poles', type=str, default=None, help="e.g. '0,0,0,0' or '0.6,0.6,0.5,0.5'")
    s.add_argument('--csv', type=str, default=None); s.add_argument('--out', type=str, default=None)
    add_eq_opts(s)

    s = sub.add_parser('observer', help='Design minimum-order observer (measured form)')
    s.add_argument('--config', type=str, default=None)
    s.add_argument('--G', type=str); s.add_argument('--H', type=str); s.add_argument('--C', type=str)
    s.add_argument('--method', type=str, choices=['acker', 'place', 'acker_ct'], default='acker')
    s.add_argument('--poles', type=str, default=None, help="'0,0' for deadbeat second order, etc.")
    s.add_argument('--csv', type=str, default=None); s.add_argument('--out', type=str, default=None)
    s.add_argument('--observer-mode', type=str, choices=['current', 'prediction'], default='current')
    add_eq_opts(s)

    s = sub.add_parser('sim', help='Simulate u = -K2 x + K1 v')
    s.add_argument('--config', type=str, default=None)
    s.add_argument('--G', type=str); s.add_argument('--H', type=str); s.add_argument('--C', type=str)
    s.add_argument('--K1', type=str); s.add_argument('--K2', type=str)
    s.add_argument('--N', type=int, default=10); s.add_argument('--ref', type=str, default='step')
    s.add_argument('--use-observer', action='store_true')
    s.add_argument('--observer-mode', type=str, choices=['current', 'prediction'], default='current')
    s.add_argument('--Ke', type=str, default=None); s.add_argument('--T', type=str, default=None)
    s.add_argument('--csv', type=str, default=None); s.add_argument('--out', type=str, default=None)
    s.add_argument('--plot', action='store_true'); s.add_argument('--savefig', type=str, default=None)
    s.add_argument('--plotly', action='store_true'); s.add_argument('--html', type=str, default=None); s.add_argument('--open', action='store_true')
    add_eq_opts(s)
    return p

def main():
    parser = build_parser()
    ns = parser.parse_args()
    app = ServoApp()

    req = RunRequest(
        mode=ns.cmd,
        config=getattr(ns, 'config', None),
        G=getattr(ns, 'G', None), H=getattr(ns, 'H', None), C=getattr(ns, 'C', None),
        which=getattr(ns, 'which', 'ogata'),
        method=getattr(ns, 'method', 'acker'),
        poles=getattr(ns, 'poles', None),
        observer_mode=getattr(ns, 'observer_mode', 'current'),
        K1=getattr(ns, 'K1', None), K2=getattr(ns, 'K2', None),
        N=getattr(ns, 'N', 10), ref=getattr(ns, 'ref', 'step'),
        use_observer=getattr(ns, 'use_observer', False),
        Ke=getattr(ns, 'Ke', None), T=getattr(ns, 'T', None),
        csv=getattr(ns, 'csv', None), out=getattr(ns, 'out', None),
        plot=getattr(ns, 'plot', False), savefig=getattr(ns, 'savefig', None),
        plotly=getattr(ns, 'plotly', False), html=getattr(ns, 'html', None), open_html=getattr(ns, 'open', False),
        eq=getattr(ns, 'eq', False), eq_stdout=getattr(ns, 'eq_stdout', False), eq_file=getattr(ns, 'eq_file', None),
    )
    res = app.run(req)
    print(json.dumps(res if isinstance(res, dict) else getattr(res, '__dict__', {'result': 'ok'}), indent=2))

if __name__ == '__main__':
    main()
