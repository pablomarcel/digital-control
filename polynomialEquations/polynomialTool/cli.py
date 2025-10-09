#!/usr/bin/env python3
from __future__ import annotations
import argparse, os, sys
if __package__ in (None, ''):
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if pkg_root not in sys.path: sys.path.insert(0, pkg_root)
    from polynomialEquations.polynomialTool.apis import RunRequest
    from polynomialEquations.polynomialTool.app import PolynomialApp
    from polynomialEquations.polynomialTool.io import parse_coeffs
else:
    from .apis import RunRequest
    from .app import PolynomialApp
    from .io import parse_coeffs

def _add_common(p):
    p.add_argument('--A', required=True); p.add_argument('--B', required=True)
    p.add_argument('--layout', choices=['ogata','desc'], default='ogata')
    p.add_argument('--d', type=int, default=0); p.add_argument('--degS', type=int); p.add_argument('--degR', type=int)
    p.add_argument('--pretty', action='store_true'); p.add_argument('--show_E', action='store_true')
    p.add_argument('--export_json'); p.add_argument('--export_csv')
    p.add_argument('--backend', choices=['mpl','plotly','none'], default='none')
    p.add_argument('--save'); p.add_argument('--T', type=float, default=1.0); p.add_argument('--kmax', type=int, default=40)
    p.add_argument('--ogata_parity', action='store_true')

def build_parser():
    ap = argparse.ArgumentParser(description='polynomialTool — Polynomial Equations (Ogata ch.7)')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p_solve = sub.add_parser('solve'); _add_common(p_solve); p_solve.add_argument('--D', required=True)
    p_pd = sub.add_parser('polydesign'); _add_common(p_pd); p_pd.add_argument('--D'); p_pd.add_argument('--H'); p_pd.add_argument('--F'); p_pd.add_argument('--config', type=int, choices=[1,2])
    p_rst = sub.add_parser('rst'); _add_common(p_rst); p_rst.add_argument('--H', required=True); p_rst.add_argument('--F', required=True); p_rst.add_argument('--rst_config', type=int, default=2, choices=[1,2])
    p_mm  = sub.add_parser('modelmatch'); _add_common(p_mm); p_mm.add_argument('--Gmodel_num', required=True); p_mm.add_argument('--Gmodel_den', required=True); p_mm.add_argument('--H1', required=True); p_mm.add_argument('--F', required=True)
    return ap

def _ns_to_req(cmd, ns) -> RunRequest:
    A = parse_coeffs(ns.A); B = parse_coeffs(ns.B)
    D = parse_coeffs(ns.D) if getattr(ns,'D',None) else None
    H = parse_coeffs(ns.H) if getattr(ns,'H',None) else None
    F = parse_coeffs(ns.F) if getattr(ns,'F',None) else None
    H1= parse_coeffs(ns.H1) if getattr(ns,'H1',None) else None
    Gm_num = parse_coeffs(ns.Gmodel_num) if getattr(ns,'Gmodel_num',None) else None
    Gm_den = parse_coeffs(ns.Gmodel_den) if getattr(ns,'Gmodel_den',None) else None
    return RunRequest(mode=cmd, A=A, B=B, layout=ns.layout, d=ns.d, degS=ns.degS, degR=ns.degR, pretty=ns.pretty, show_E=ns.show_E,
                      export_json=ns.export_json, export_csv=ns.export_csv, backend=ns.backend, save=ns.save, T=ns.T, kmax=ns.kmax,
                      D=D, H=H, F=F, config=getattr(ns,'config',None), ogata_parity=ns.ogata_parity, Gmodel_num=Gm_num, Gmodel_den=Gm_den, H1=H1, rst_config=getattr(ns,'rst_config',2))

def main():
    parser = build_parser(); ns = parser.parse_args(); req = _ns_to_req(ns.cmd, ns)
    app = PolynomialApp(); res = app.run(req)
    if 'alpha' in res and 'beta' in res:
        import numpy as np
        print('alpha:', np.round(res['alpha'],12)); print('beta :', np.round(res['beta'],12))

if __name__ == '__main__': main()
