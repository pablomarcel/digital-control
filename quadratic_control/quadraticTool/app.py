from __future__ import annotations

import os
import numpy as np

from .apis import RunRequest
from .io import load_yaml, save_csv_vector, save_csv_matrix, write_text
from .design import plot_series_mpl, plot_series_plotly
from .core import (
    FiniteHorizonLQR,
    CTtoDTWeights,
    SteadyStateLQR,
    ServoLQR,
    LyapunovAnalyzer,
    LyapunovSweep,
    substitute_params_matrix,
)


class QuadraticApp:
    def __init__(self) -> None:
        self.titles = {
            "fh-dt": "Finite-horizon DT LQR",
            "ct-siso-ogata": "CT SISO → DT weights (Ogata Ex. 8-2) + FH solve",
            "ss-lqr": "Steady-state DT LQR (DARE)",
            "servo-lqr": "Servo LQR (integral augmentation)",
            "lyap": "Lyapunov (G'PG - P = -Q)",
            "lyap-sweep": "Lyapunov parameter sweep",
        }

    def _maybe_sub(self, template, params: dict[str, float]):
        """Convert a YAML-loaded matrix/vector that may contain param strings into floats."""
        arr = np.asarray(template, dtype=object)
        if arr.dtype == object and any(isinstance(x, str) for x in arr.flat):
            return substitute_params_matrix(arr, params)
        return np.asarray(template, dtype=float)

    def run(self, req: RunRequest) -> str:
        if req.mode in {"fh-dt", "ct-siso-ogata", "ss-lqr", "servo-lqr", "lyap", "lyap-sweep"}:
            return self._run_yaml(req)
        raise ValueError(f"Unknown mode: {req.mode}")

    def _run_yaml(self, req: RunRequest) -> str:
        assert req.infile is not None, "YAML infile required"
        cfg = load_yaml(req.infile)
        params = dict(cfg.get("params", {}))
        if req.params:
            params.update({k: float(v) for k, v in req.params.items()})
        out_case = os.path.join(req.outdir, req.name)
        os.makedirs(out_case, exist_ok=True)

        mode = cfg.get("mode", req.mode)

        if mode == "fh-dt":
            G = self._maybe_sub(cfg["G"], params)
            H = self._maybe_sub(cfg["H"], params)
            Q = self._maybe_sub(cfg["Q"], params)
            R = self._maybe_sub(cfg["R"], params)
            n = int(G.shape[0])
            S = self._maybe_sub(cfg.get("S", np.zeros((n, n))), params)
            N = int(cfg["N"])
            M = self._maybe_sub(cfg.get("M", np.zeros((n, H.shape[1]))), params)
            x0 = self._maybe_sub(cfg.get("x0", np.zeros(n)), params)

            res = FiniteHorizonLQR().solve(G, H, Q, R, N, S, M, x0)
            save_csv_vector(os.path.join(out_case, "K.csv"), [float(k.squeeze()) for k in res.K_seq])
            if res.P_seq[0].shape == (1, 1):
                save_csv_vector(os.path.join(out_case, "P.csv"), [float(p.squeeze()) for p in res.P_seq])
            else:
                save_csv_matrix(os.path.join(out_case, "P0.csv"), res.P_seq[0])
            save_csv_vector(os.path.join(out_case, "x.csv"), [float(x.squeeze()) for x in res.x_seq])
            save_csv_vector(os.path.join(out_case, "u.csv"), [float(u.squeeze()) for u in res.u_seq])
            write_text(os.path.join(out_case, "summary.txt"), f"{self.titles[mode]}\nJ={res.J}\n")

            if req.plot in ("mpl", "plotly"):
                series = {
                    "x(k)": np.array([float(x.squeeze()) for x in res.x_seq[:-1]]),
                    "u(k)": np.array([float(u.squeeze()) for u in res.u_seq]),
                }
                if req.plot == "mpl":
                    plot_series_mpl(series, f"{req.name}: x & u", os.path.join(out_case, "x_u.png"))
                else:
                    plot_series_plotly(series, f"{req.name}: x & u", os.path.join(out_case, "x_u.html"))

        elif mode == "ct-siso-ogata":
            a = float(params.get("a", cfg["a"]))
            b = float(params.get("b", cfg["b"]))
            T = float(params.get("T", cfg["T"]))
            N = int(cfg["N"])
            x0 = float(cfg.get("x0", 1.0))
            Sterm = float(cfg.get("S", 1.0))
            disc = CTtoDTWeights().siso_ogata(a, b, T)
            res = FiniteHorizonLQR().solve(
                disc.G, disc.H, disc.Q1, disc.R1, N, np.array([[Sterm]]), disc.M1, np.array([[x0]])
            )
            save_csv_vector(os.path.join(out_case, "K.csv"), [float(k.squeeze()) for k in res.K_seq])
            save_csv_vector(os.path.join(out_case, "x.csv"), [float(x.squeeze()) for x in res.x_seq])
            save_csv_vector(os.path.join(out_case, "u.csv"), [float(u.squeeze()) for u in res.u_seq])
            write_text(os.path.join(out_case, "summary.txt"), f"{self.titles[mode]}\nJ={res.J}\n")

            if req.plot in ("mpl", "plotly"):
                series = {
                    "x(k)": np.array([float(x.squeeze()) for x in res.x_seq[:-1]]),
                    "u(k)": np.array([float(u.squeeze()) for u in res.u_seq]),
                }
                if req.plot == "mpl":
                    plot_series_mpl(series, f"{req.name}: x & u", os.path.join(out_case, "x_u.png"))
                else:
                    plot_series_plotly(series, f"{req.name}: x & u", os.path.join(out_case, "x_u.html"))

        elif mode == "ss-lqr":
            G = self._maybe_sub(cfg["G"], params)
            H = self._maybe_sub(cfg["H"], params)
            Q = self._maybe_sub(cfg["Q"], params)
            R = self._maybe_sub(cfg["R"], params)
            res = SteadyStateLQR().solve(G, H, Q, R)
            save_csv_matrix(os.path.join(out_case, "P.csv"), res.P)
            save_csv_matrix(os.path.join(out_case, "K.csv"), res.K)
            write_text(os.path.join(out_case, "summary.txt"), f"{self.titles[mode]}\n")

        elif mode == "servo-lqr":
            G = self._maybe_sub(cfg["G"], params)
            H = self._maybe_sub(cfg["H"], params)
            C = self._maybe_sub(cfg["C"], params)
            Qx = self._maybe_sub(cfg["Qx"], params)
            Qi = self._maybe_sub(cfg["Qi"], params)
            R = self._maybe_sub(cfg["R"], params)
            steps = int(cfg.get("steps", 101))
            r_amp = float(cfg.get("r", 1.0))
            x0 = np.asarray(cfg.get("x0", np.zeros(G.shape[0])), dtype=float).reshape(-1)
            v0 = float(cfg.get("v0", 0.0))
            D = float(cfg.get("D", 0.0))

            res = ServoLQR().solve(G, H, C, Qx, Qi, R)
            n = G.shape[0]
            Kx = np.asarray(res.K_full[:, :n], dtype=float)
            Ki_ogata = -np.asarray(res.K_full[:, n:], dtype=float)
            save_csv_matrix(os.path.join(out_case, "P.csv"), res.P)
            save_csv_matrix(os.path.join(out_case, "Kx.csv"), Kx)
            save_csv_matrix(os.path.join(out_case, "Ki.csv"), Ki_ogata)
            save_csv_matrix(os.path.join(out_case, "K_full.csv"), res.K_full)
            write_text(os.path.join(out_case, "summary.txt"), f"{self.titles[mode]}\nKi uses Ogata sign.\n")

            # simulate (SISO)
            m = Kx.shape[0]
            assert m == 1
            x = x0.copy()
            v = v0
            y_series = [float(C @ x + D * 0.0)]
            u_series: list[float] = []
            x_series = [float(x[0])]
            if n >= 2:
                x2_series = [float(x[1])]
            Kx_row = Kx.reshape(-1)
            Ki_val = float(Ki_ogata.squeeze())
            for _ in range(steps - 1):
                u = -float(Kx_row @ x) + Ki_val * v
                x = (G @ x.reshape(-1, 1) + H * u).reshape(-1)
                y = float(C @ x + D * u)
                v = v + r_amp - y
                u_series.append(float(u))
                y_series.append(float(y))
                x_series.append(float(x[0]))
                if n >= 2:
                    x2_series.append(float(x[1]))

            save_csv_vector(os.path.join(out_case, "y.csv"), y_series)
            save_csv_vector(os.path.join(out_case, "u.csv"), u_series)
            save_csv_vector(os.path.join(out_case, "x1.csv"), x_series)
            if n >= 2:
                save_csv_vector(os.path.join(out_case, "x2.csv"), x2_series)

            if req.plot in ("mpl", "plotly"):
                series = {
                    "y(k)": np.asarray(y_series),
                    "u(k)": np.asarray(u_series + ([u_series[-1]] if u_series else [0.0])),
                }
                if req.plot == "mpl":
                    plot_series_mpl(series, f"{req.name}: y & u", os.path.join(out_case, "y_u.png"))
                else:
                    plot_series_plotly(series, f"{req.name}: y & u", os.path.join(out_case, "y_u.html"))

        elif mode == "lyap":
            Gt = np.asarray(cfg["G"], dtype=object)
            Qt = np.asarray(cfg["Q"], dtype=object)
            x0 = cfg.get("x0", None)
            if params:
                G = substitute_params_matrix(Gt, params)
                Q = substitute_params_matrix(Qt, params)
            else:
                G = np.asarray(Gt, dtype=float)
                Q = np.asarray(Qt, dtype=float)
            res = LyapunovAnalyzer().solve(G, Q, x0)
            save_csv_matrix(os.path.join(out_case, "P.csv"), res.P)
            if res.J is not None:
                write_text(os.path.join(out_case, "summary.txt"), f"{self.titles[mode]}\nJ={res.J}\n")
            else:
                write_text(os.path.join(out_case, "summary.txt"), f"{self.titles[mode]}\n")

        elif mode == "lyap-sweep":
            if req.sweep:
                pname, rng = req.sweep.split("=", 1)
                s, t, p = rng.split(":")
                start = float(s)
                stop = float(t)
                pts = int(p)
            else:
                sweep_cfg = cfg.get("sweep", {})
                pname = sweep_cfg.get("name")
                start = float(sweep_cfg.get("start"))
                stop = float(sweep_cfg.get("stop"))
                pts = int(sweep_cfg.get("points"))

            Gt = np.asarray(cfg["G"], dtype=object)
            Qt = np.asarray(cfg["Q"], dtype=object)
            x0 = cfg.get("x0", None)

            # substitute other params (not the sweep var) if present
            fixed = {k: v for k, v in params.items() if k != pname}
            if fixed:
                Gt = substitute_params_matrix(Gt, fixed)
                Qt = substitute_params_matrix(Qt, fixed)

            res = LyapunovSweep().solve(Gt, Qt, pname, start, stop, pts, x0)

            # Always save the sweep grid and all Js (inf means invalid/unstable point)
            save_csv_vector(os.path.join(out_case, f"{pname}_grid.csv"), [float(x) for x in res.grid])
            save_csv_vector(os.path.join(out_case, "J.csv"), [float(x) for x in res.Js])

            # Save P* only if it exists (there may be no stable/solvable points)
            if res.P_star is not None:
                save_csv_matrix(os.path.join(out_case, "P_star.csv"), res.P_star)

            a_star_text = "None" if res.a_star is None else f"{res.a_star}"
            J_min_text = "None" if res.J_min is None else f"{res.J_min}"
            write_text(
                os.path.join(out_case, "summary.txt"),
                f"{self.titles[mode]}\n{pname}*={a_star_text}\nJ_min={J_min_text}\n",
            )

        else:
            raise ValueError(f"Unknown mode {mode}")

        return out_case
