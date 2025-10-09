
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .apis import (
    DesignRequest, ClosedLoopRequest, K0Request, SelectRequest, SimRequest, ExampleRequest
)
from .design import (
    design_observer, closedloop_poles, compute_k0, select_L, simulate
)
from .io import parse_matrix
from .utils import eigvals_sorted, asjson


@dataclass
class ObserverApp:
    def run(self, req: Any) -> Dict[str, Any]:
        if isinstance(req, DesignRequest):
            return design_observer(
                req.kind, req.A, req.C, poles=req.poles, B=req.B, method=req.method,
                G=req.G, Qn=req.Qn, Rn=req.Rn, csv=req.csv, out=req.out
            )
        if isinstance(req, ClosedLoopRequest):
            return closedloop_poles(req.A, req.B, req.C, req.K, req.L, out=req.out)
        if isinstance(req, K0Request):
            return compute_k0(req.A, req.B, req.C, req.K, L=req.L, mode=req.mode,
                              ogata_extra_gain=req.ogata_extra_gain, out=req.out)
        if isinstance(req, SelectRequest):
            return select_L(req.A, req.B, req.C, req.K, method=req.method,
                            rule_of_thumb=req.rule_of_thumb, speedup=req.speedup,
                            sweep=req.sweep, steps=req.steps, dlqe=req.dlqe,
                            G=req.G, Qn=req.Qn, Rn=req.Rn, csv=req.csv, out=req.out)
        if isinstance(req, SimRequest):
            return simulate(req.A, req.B, req.C, req.K, req.L, N=req.N, Ts=req.Ts,
                            ref=req.ref, K0=req.K0, k0_mode=req.k0_mode,
                            ogata_extra_gain=req.ogata_extra_gain, csv=req.csv,
                            out=req.out, plot=req.plot, plot_type=req.plot_type,
                            plotly=req.plotly, html=req.html)
        if isinstance(req, ExampleRequest):
            return self._run_example(req)
        raise TypeError(f"Unsupported request type: {type(req)}")

    # textbook examples for parity with the original script
    def _run_example(self, req: ExampleRequest) -> Dict[str, Any]:
        import numpy as np
        which = req.which
        if which == "6-9":
            A = np.array([[0.0, -0.16],[1.0, -1.0]]); C = np.array([[0.0, 1.0]])
            from .core import design_prediction_observer
            L = design_prediction_observer(A, C, [0.5+0.5j, 0.5-0.5j], method="acker")
            return {"Example": "6-9", "L": L, "eig(A-LC)": eigvals_sorted(A - L @ C)}
        elif which == "6-10":
            T = float(req.Ts)
            A = np.array([[1.0, T],[0.0, 1.0]]); C = np.array([[1.0, 0.0]])
            from .core import design_prediction_observer
            L = design_prediction_observer(A, C, [0,0], method="acker")
            return {"Example": "6-10", "L (deadbeat)": L, "theoretical": [[2.0],[1.0/T]]}
        elif which == "6-11":
            T = 0.2
            A = np.array([[1.0, T],[0.0, 1.0]]); B = np.array([[T*T/2],[T]]); C = np.array([[1.0, 0.0]])
            from .core import design_minimum_order_observer
            d = design_minimum_order_observer(A, B, C, poles=[0], method="acker")
            return {"Example": "6-11", "Ke (expected ~5)": d.Ke, "min-order err poles": list(d.err_poles)}
        elif which == "6-12":
            Ts = 0.2
            A = np.array([[1.0, Ts],[0.0, 1.0]]); B = np.array([[Ts*Ts/2],[Ts]]); C = np.array([[1.0, 0.0]])
            from .core import design_prediction_observer, k0_state, simulate_full_observer
            K = np.array([[8.0, 3.2]])
            L = design_prediction_observer(A, C, [0.0, 0.0], method="acker")
            K0 = k0_state(A, B, C, K)
            res = simulate_full_observer(A, B, C, K, L, N=41, r=np.ones((41,1)), Ts=Ts, K0=K0)
            y_end = float(np.squeeze(np.array(res["y"]))[-1])
            return {"Example": "6-12", "K0 (book ~6.0606)": K0, "y_end": y_end}
        else:
            raise ValueError("Unknown example. Use 6-9, 6-10, 6-11, or 6-12.")
