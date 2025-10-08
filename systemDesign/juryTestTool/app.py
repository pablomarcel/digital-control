
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any

import sympy as sp

from .apis import RunRequest, RunResult, MethodResult
from .io import load_from_json, poly_from_coeffs, dump_table, dump_json
from .utils import sstr
from .core import Tolerances
from .design import StabilityDesigner

@dataclass
class JuryTestApp:
    def run(self, req: RunRequest) -> RunResult:
        # Build polynomial
        if req.json_in:
            z, K, P, a_fwd = load_from_json(req.json_in, req.rational)
        else:
            tokens = [t for t in req.coeffs.replace(",", " ").split() if t]
            z, K, P, a_fwd = poly_from_coeffs(tokens, var_name="z", param_name=None, rational=req.rational)

        n = len(a_fwd) - 1
        tols = Tolerances(abs_tol=req.abs_tol, rel_tol=req.rel_tol, unit_tol=req.unit_tol)
        subs_eval = ({K: float(req.eval_K)} if (req.eval_K is not None and K is not None) else None)

        designer = StabilityDesigner(tols)
        methods_out, eval_summary = designer.run_methods(req.method, P, a_fwd, z, K, subs_eval, req.solve_range, req.T)

        # Save artifacts if requested
        if req.save_table:
            table_txt = ""
            for mname, payload in methods_out.items():
                table_txt += f"\n=== {mname.upper()} ===\n" + "-"*78 + "\n" + payload["text"] + "\n"
            dump_table(table_txt, req.save_table)

        if req.save_json:
            report = {
                "polynomial": sp.sstr(sp.expand(P)),
                "order": int(n),
                "coeffs_high_to_const": [sp.sstr(c) for c in a_fwd],
                "parameter": sp.sstr(K) if K is not None else None,
                "methods": {k: {kk:v for kk,v in d.items() if kk != "text"} for k,d in methods_out.items()},
                "eval": eval_summary
            }
            dump_json(report, req.save_json)

        return RunResult(
            order=int(n),
            polynomial=sp.sstr(sp.expand(P)),
            coeffs_high_to_const=[sp.sstr(c) for c in a_fwd],
            parameter=(sp.sstr(K) if K is not None else None),
            methods={k: MethodResult(verdict=d["verdict"], details={kk:v for kk,v in d.items() if kk != "text"}) for k,d in methods_out.items()},
            eval_summary=eval_summary
        )
