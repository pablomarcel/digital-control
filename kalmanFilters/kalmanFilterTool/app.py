from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .apis import RunRequest
from .core import default_cv_model, coerce_shapes, Simulator
from .design import CSVExporter, Plotter
from .utils import out_path

@dataclass
class KalmanFilterApp:
    def build_and_run(self, req: RunRequest) -> dict:
        # Defaults then overrides
        if req.A is None or req.B is None or req.C is None or req.G is None or req.Q is None or req.R is None:
            A,B,C,G,Q_state,R = default_cv_model(req.dt, req.q, req.r)
        if req.A is not None: A = req.A
        if req.B is not None: B = req.B
        if req.C is not None: C = req.C
        if req.G is not None: G = req.G
        Q_arg_was_none = req.Q is None
        Q = Q_state if Q_arg_was_none else req.Q
        R = R if req.R is None else req.R

        model = coerce_shapes(A,B,C,G,Q,R, req.dt, req.q, Q_arg_was_none)
        n = A.shape[0]
        x0     = req.x0 if req.x0 is not None else np.zeros((n,1))
        P0     = req.P0 if req.P0 is not None else np.eye(n)*100.0
        xtrue0 = req.xtrue0 if req.xtrue0 is not None else np.zeros((n,1))

        sim = Simulator(model=model, dt=req.dt, T=req.T, seed=req.seed, steady=req.steady, u=req.u)
        result = sim.run(x0, P0, xtrue0)

        if req.save_csv:
            csv_path = CSVExporter(req.out_dir).write(result.t, result.Y_meas, result.X_true, result.X_hat, req.save_csv)
            print(f"Wrote {csv_path}")
        plotter = Plotter(backend=req.backend, out_dir=req.out_dir, no_show=req.no_show)
        if req.backend != "none":
            plotter.render(result.t, result.Y_meas, result.X_true, result.X_hat, req.save_png, req.save_html)

        import json
        meta_path = out_path(req.out_dir, "kf_meta.json", "kf_meta.json")
        with open(meta_path, "w", encoding="utf-8") as fh:
            json.dump(result.meta, fh, indent=2)
        print(f"Wrote {meta_path}")
        return {"meta_path": meta_path}
