from __future__ import annotations
from typing import Dict, Any
from .apis import RunRequest
from .design import polydesign, rst_design, model_match, solve_alpha_beta

class PolynomialApp:
    def run(self, req: RunRequest) -> Dict[str, Any]:
        if req.mode=='solve':
            if req.D is None: raise ValueError('solve mode requires D')
            return solve_alpha_beta(req.A, req.B, req.D, req.d, req.degS, req.degR, req.layout)
        if req.mode=='polydesign':
            return polydesign(req.A, req.B, req.D, req.H, req.F, req.d, req.degS, req.degR, req.layout,
                              req.pretty, req.show_E, req.backend, req.save, req.T, req.kmax, req.config,
                              req.export_json, req.export_csv, req.ogata_parity)
        if req.mode=='rst':
            if req.H is None or req.F is None: raise ValueError('rst mode requires H and F')
            return rst_design(req.A, req.B, req.H, req.F, req.d, req.degS, req.degR, req.layout,
                              req.rst_config, req.backend, req.save, req.T, req.kmax, req.export_json,
                              req.pretty, req.ogata_parity)
        if req.mode=='modelmatch':
            if req.Gmodel_num is None or req.Gmodel_den is None or req.H1 is None or req.F is None:
                raise ValueError('modelmatch requires Gmodel_num, Gmodel_den, H1, F')
            return model_match(req.A, req.B, req.Gmodel_num, req.Gmodel_den, req.H1, req.F,
                               req.d, req.degS, req.degR, req.layout, req.backend, req.save, req.T, req.kmax,
                               req.export_json, req.pretty)
        raise ValueError(f'Unknown mode: {req.mode}')
