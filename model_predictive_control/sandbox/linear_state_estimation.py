#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
linear_state_estimation.py

Sandbox for Rawlings/Mayne/Diehl, Section 1.4.2: Linear Optimal State Estimation.

What this script does
---------------------
It implements the linear Gaussian state estimator recursion used in Section 1.4.2:

    Measurement update:
        innovation_k = y_k - C xhat_minus_k
        S_k          = C P_minus_k C.T + R
        L_k          = P_minus_k C.T S_k^{-1}
        xhat_k       = xhat_minus_k + L_k innovation_k
        P_k          = P_minus_k - P_minus_k C.T S_k^{-1} C P_minus_k

    Forecast step:
        xhat_minus_{k+1} = A xhat_k + B u_k
        P_minus_{k+1}    = A P_k A.T + G Qw G.T

The textbook's compact derivation in Section 1.4.2 suppresses known inputs in the
forecast expression. For engineering use, this script includes the known input term
B u_k. Set B or u to zero to recover the no-known-input form.

Outputs
-------
Default output directory:
    out/linear_state_estimation

The script writes:
    linear_state_estimation_results.json
    linear_state_estimation_timeseries.csv
    linear_state_estimation_calculation_log.txt
    linear_state_estimation_states.png
    linear_state_estimation_errors.png
    linear_state_estimation_covariance.png
    linear_state_estimation_innovation_gain.png

Run
---
    python linear_state_estimation.py

Optional:
    python linear_state_estimation.py --steps 80 --seed 12 --out out/linear_state_estimation
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import argparse
import csv
import json

import numpy as np


@dataclass(frozen=True)
class LinearEstimatorProblem:
    """Container for one linear Gaussian estimation sandbox."""

    A: np.ndarray
    B: np.ndarray
    C: np.ndarray
    G: np.ndarray
    Qw: np.ndarray
    R: np.ndarray
    x0_mean: np.ndarray
    P0: np.ndarray
    x0_true: np.ndarray
    U: np.ndarray
    dt: float
    state_names: list[str]
    output_names: list[str]
    input_names: list[str]

    @property
    def nx(self) -> int:
        return int(self.A.shape[0])

    @property
    def nu(self) -> int:
        return int(self.B.shape[1])

    @property
    def ny(self) -> int:
        return int(self.C.shape[0])

    @property
    def steps(self) -> int:
        return int(self.U.shape[0])


def arr(value: Any) -> np.ndarray:
    """Return a float NumPy array."""

    return np.asarray(value, dtype=float)


def mat_to_str(M: np.ndarray, precision: int = 6) -> str:
    """Compact matrix string for calculation logs."""

    return np.array2string(np.asarray(M, dtype=float), precision=precision, suppress_small=False)


def as_jsonable(value: Any) -> Any:
    """Convert NumPy values to JSON-safe Python values."""

    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    return value


def default_problem(steps: int = 70) -> LinearEstimatorProblem:
    """Build a small double-integrator tracking example with noisy position measurements."""

    dt = 0.1

    # Discrete-time double integrator:
    #   x1 = position
    #   x2 = velocity
    #   u  = known acceleration command
    A = arr([[1.0, dt], [0.0, 1.0]])
    B = arr([[0.5 * dt * dt], [dt]])
    C = arr([[1.0, 0.0]])

    # Process disturbance enters acceleration-like channel.
    # x_{k+1} = A x_k + B u_k + G w_k
    G = arr([[0.5 * dt * dt], [dt]])

    # w variance and measurement variance.
    # Larger Qw means we trust the model forecast less.
    # Larger R means we trust the measurement less.
    Qw = arr([[0.16]])
    R = arr([[0.09]])

    # Prior: intentionally uncertain, especially velocity.
    x0_mean = arr([0.0, 0.0])
    P0 = arr([[9.0, 0.0], [0.0, 4.0]])

    # True initial state used only to generate synthetic measurements.
    x0_true = arr([2.5, -0.2])

    t = np.arange(steps) * dt
    U = (0.55 * np.sin(0.45 * t) - 0.25 * (t > 3.0)).reshape(-1, 1)

    return LinearEstimatorProblem(
        A=A,
        B=B,
        C=C,
        G=G,
        Qw=Qw,
        R=R,
        x0_mean=x0_mean,
        P0=P0,
        x0_true=x0_true,
        U=U,
        dt=dt,
        state_names=["position", "velocity"],
        output_names=["measured_position"],
        input_names=["acceleration_command"],
    )


def simulate_truth(problem: LinearEstimatorProblem, seed: int) -> dict[str, np.ndarray]:
    """Generate one repeatable true trajectory and noisy measurement sequence."""

    rng = np.random.default_rng(seed)
    X_true = np.zeros((problem.steps + 1, problem.nx))
    Y = np.zeros((problem.steps, problem.ny))
    W = np.zeros((problem.steps, problem.Qw.shape[0]))
    V = np.zeros((problem.steps, problem.ny))
    X_true[0] = problem.x0_true

    for k in range(problem.steps):
        W[k] = rng.multivariate_normal(np.zeros(problem.Qw.shape[0]), problem.Qw)
        V[k] = rng.multivariate_normal(np.zeros(problem.ny), problem.R)
        Y[k] = problem.C @ X_true[k] + V[k]
        X_true[k + 1] = problem.A @ X_true[k] + problem.B @ problem.U[k] + problem.G @ W[k]

    return {"X_true": X_true, "Y": Y, "W": W, "V": V}


def kalman_filter(problem: LinearEstimatorProblem, Y: np.ndarray) -> dict[str, np.ndarray]:
    """Run the Section 1.4.2 update/forecast recursion."""

    nx, ny, steps = problem.nx, problem.ny, problem.steps
    xhat_minus = np.zeros((steps + 1, nx))
    xhat = np.zeros((steps, nx))
    P_minus = np.zeros((steps + 1, nx, nx))
    P = np.zeros((steps, nx, nx))
    L = np.zeros((steps, nx, ny))
    S = np.zeros((steps, ny, ny))
    innovation = np.zeros((steps, ny))

    xhat_minus[0] = problem.x0_mean
    P_minus[0] = problem.P0

    for k in range(steps):
        # Measurement update: combine the forecast distribution with y(k).
        innovation[k] = Y[k] - problem.C @ xhat_minus[k]
        S[k] = problem.C @ P_minus[k] @ problem.C.T + problem.R
        L[k] = P_minus[k] @ problem.C.T @ np.linalg.inv(S[k])
        xhat[k] = xhat_minus[k] + L[k] @ innovation[k]
        P[k] = P_minus[k] - P_minus[k] @ problem.C.T @ np.linalg.inv(S[k]) @ problem.C @ P_minus[k]
        P[k] = 0.5 * (P[k] + P[k].T)  # numerical symmetry cleanup

        # Forecast: propagate the current conditional normal through the model.
        xhat_minus[k + 1] = problem.A @ xhat[k] + problem.B @ problem.U[k]
        P_minus[k + 1] = problem.A @ P[k] @ problem.A.T + problem.G @ problem.Qw @ problem.G.T
        P_minus[k + 1] = 0.5 * (P_minus[k + 1] + P_minus[k + 1].T)

    return {
        "xhat_minus": xhat_minus,
        "xhat": xhat,
        "P_minus": P_minus,
        "P": P,
        "L": L,
        "S": S,
        "innovation": innovation,
    }


def forecast_from_last_estimate(problem: LinearEstimatorProblem, xhat_last: np.ndarray, P_last: np.ndarray, future_steps: int = 20) -> dict[str, np.ndarray]:
    """Forecast beyond the final measurement using the model only."""

    nx = problem.nx
    Xf = np.zeros((future_steps + 1, nx))
    Pf = np.zeros((future_steps + 1, nx, nx))
    Xf[0] = xhat_last
    Pf[0] = P_last

    if problem.steps:
        u_hold = problem.U[-1]
    else:
        u_hold = np.zeros(problem.nu)

    for j in range(future_steps):
        Xf[j + 1] = problem.A @ Xf[j] + problem.B @ u_hold
        Pf[j + 1] = problem.A @ Pf[j] @ problem.A.T + problem.G @ problem.Qw @ problem.G.T
        Pf[j + 1] = 0.5 * (Pf[j + 1] + Pf[j + 1].T)

    return {"forecast_x": Xf, "forecast_P": Pf, "forecast_u_hold": u_hold}


def make_calculation_log(
    problem: LinearEstimatorProblem,
    truth: dict[str, np.ndarray],
    filt: dict[str, np.ndarray],
    forecast: dict[str, np.ndarray],
    max_steps: int = 8,
) -> str:
    """Create a plain-English plus matrix-calculation log."""

    lines: list[str] = []
    lines.append("Linear Optimal State Estimation Calculation Log")
    lines.append("Rawlings/Mayne/Diehl Section 1.4.2 sandbox")
    lines.append("")
    lines.append("Model used in this script")
    lines.append("  x(k+1) = A x(k) + B u(k) + G w(k),      w(k) ~ N(0, Qw)")
    lines.append("  y(k)   = C x(k) + v(k),                v(k) ~ N(0, R)")
    lines.append("  Known input B u(k) is included for engineering use.")
    lines.append("")
    lines.append("Matrices")
    for name, M in [("A", problem.A), ("B", problem.B), ("C", problem.C), ("G", problem.G), ("Qw", problem.Qw), ("R", problem.R), ("xhat_minus(0)", problem.x0_mean), ("P_minus(0)", problem.P0)]:
        lines.append(f"{name} = {mat_to_str(M)}")
    lines.append("")
    lines.append("Recursion used")
    lines.append("  innovation(k) = y(k) - C xhat_minus(k)")
    lines.append("  S(k)          = C P_minus(k) C.T + R")
    lines.append("  L(k)          = P_minus(k) C.T inv(S(k))")
    lines.append("  xhat(k)       = xhat_minus(k) + L(k) innovation(k)")
    lines.append("  P(k)          = P_minus(k) - P_minus(k) C.T inv(S(k)) C P_minus(k)")
    lines.append("  xhat_minus(k+1) = A xhat(k) + B u(k)")
    lines.append("  P_minus(k+1)    = A P(k) A.T + G Qw G.T")
    lines.append("")

    Y = truth["Y"]
    X_true = truth["X_true"]
    xhat_minus = filt["xhat_minus"]
    xhat = filt["xhat"]
    P_minus = filt["P_minus"]
    P = filt["P"]
    L = filt["L"]
    S = filt["S"]
    innovation = filt["innovation"]
    nlog = min(max_steps, problem.steps)

    for k in range(nlog):
        lines.append("-" * 78)
        lines.append(f"Step k = {k}")
        lines.append(f"u({k}) = {mat_to_str(problem.U[k])}")
        lines.append(f"true x({k}) = {mat_to_str(X_true[k])}")
        lines.append(f"measurement y({k}) = {mat_to_str(Y[k])}")
        lines.append("")
        lines.append("Measurement update")
        lines.append(f"xhat_minus({k}) = {mat_to_str(xhat_minus[k])}")
        lines.append(f"P_minus({k}) = {mat_to_str(P_minus[k])}")
        lines.append(f"innovation({k}) = y - C xhat_minus = {mat_to_str(innovation[k])}")
        lines.append(f"S({k}) = C P_minus C.T + R = {mat_to_str(S[k])}")
        lines.append(f"L({k}) = P_minus C.T inv(S) = {mat_to_str(L[k])}")
        lines.append(f"xhat({k}) = xhat_minus + L innovation = {mat_to_str(xhat[k])}")
        lines.append(f"P({k}) = {mat_to_str(P[k])}")
        lines.append("")
        lines.append("Forecast")
        lines.append(f"xhat_minus({k+1}) = A xhat({k}) + B u({k}) = {mat_to_str(xhat_minus[k+1])}")
        lines.append(f"P_minus({k+1}) = A P({k}) A.T + G Qw G.T = {mat_to_str(P_minus[k+1])}")
        lines.append(f"estimation error after update = true x({k}) - xhat({k}) = {mat_to_str(X_true[k] - xhat[k])}")
        lines.append("")

    lines.append("-" * 78)
    lines.append("Forecast beyond final measurement")
    lines.append(f"Held input for forecast = {mat_to_str(forecast['forecast_u_hold'])}")
    for j in range(min(8, forecast["forecast_x"].shape[0])):
        lines.append(
            f"forecast step +{j}: mean = {mat_to_str(forecast['forecast_x'][j])}, "
            f"diag(P) = {mat_to_str(np.diag(forecast['forecast_P'][j]))}"
        )
    lines.append("")
    lines.append("Engineering interpretation")
    lines.append("  xhat_minus is the model forecast before the next measurement is used.")
    lines.append("  innovation is the measurement surprise: measured output minus forecasted output.")
    lines.append("  L is the estimator gain. Large L means the measurement can move the estimate strongly.")
    lines.append("  P_minus usually grows during forecasting because process noise is injected.")
    lines.append("  P usually shrinks after a measurement update because measurement information is added.")
    return "\n".join(lines) + "\n"


def write_outputs(
    out_dir: Path,
    problem: LinearEstimatorProblem,
    truth: dict[str, np.ndarray],
    filt: dict[str, np.ndarray],
    forecast: dict[str, np.ndarray],
    log_text: str,
) -> dict[str, Path]:
    """Write JSON, CSV, TXT, and plot files."""

    out_dir.mkdir(parents=True, exist_ok=True)
    stem = "linear_state_estimation"
    paths: dict[str, Path] = {}

    X_true = truth["X_true"]
    Y = truth["Y"]
    U = problem.U
    xhat_minus = filt["xhat_minus"]
    xhat = filt["xhat"]
    P_minus = filt["P_minus"]
    P = filt["P"]
    L = filt["L"]
    innovation = filt["innovation"]

    result = {
        "title": "Linear Optimal State Estimation - Section 1.4.2 Sandbox",
        "model": {
            "A": problem.A,
            "B": problem.B,
            "C": problem.C,
            "G": problem.G,
            "Qw": problem.Qw,
            "R": problem.R,
            "dt": problem.dt,
        },
        "prior": {"x0_mean": problem.x0_mean, "P0": problem.P0, "x0_true_for_synthetic_data": problem.x0_true},
        "state_names": problem.state_names,
        "output_names": problem.output_names,
        "input_names": problem.input_names,
        "time": np.arange(problem.steps + 1) * problem.dt,
        "time_y": np.arange(problem.steps) * problem.dt,
        "U": U,
        "Y": Y,
        "X_true": X_true,
        "xhat_minus": xhat_minus,
        "xhat": xhat,
        "P_minus": P_minus,
        "P": P,
        "L": L,
        "innovation": innovation,
        "forecast_from_final_estimate": forecast,
        "final_update_error": X_true[problem.steps - 1] - xhat[-1],
        "final_forecast_mean_next_sample": xhat_minus[-1],
        "final_forecast_covariance_next_sample": P_minus[-1],
    }

    json_path = out_dir / f"{stem}_results.json"
    json_path.write_text(json.dumps(as_jsonable(result), indent=2), encoding="utf-8")
    paths["json"] = json_path

    log_path = out_dir / f"{stem}_calculation_log.txt"
    log_path.write_text(log_text, encoding="utf-8")
    paths["calculation_log"] = log_path

    csv_path = out_dir / f"{stem}_timeseries.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        header = [
            "k", "time", "u_accel_cmd", "y_measured_position",
            "x_true_position", "x_true_velocity",
            "xhat_minus_position", "xhat_minus_velocity",
            "xhat_position", "xhat_velocity",
            "error_position", "error_velocity",
            "innovation", "gain_position", "gain_velocity",
            "Pminus_pos_var", "Pminus_vel_var", "P_pos_var", "P_vel_var",
        ]
        writer.writerow(header)
        for k in range(problem.steps):
            err = X_true[k] - xhat[k]
            writer.writerow([
                k, k * problem.dt, U[k, 0], Y[k, 0],
                X_true[k, 0], X_true[k, 1],
                xhat_minus[k, 0], xhat_minus[k, 1],
                xhat[k, 0], xhat[k, 1],
                err[0], err[1],
                innovation[k, 0], L[k, 0, 0], L[k, 1, 0],
                P_minus[k, 0, 0], P_minus[k, 1, 1], P[k, 0, 0], P[k, 1, 1],
            ])
    paths["csv"] = csv_path

    paths.update(make_plots(out_dir, stem, problem, truth, filt, forecast))
    return paths


def make_plots(
    out_dir: Path,
    stem: str,
    problem: LinearEstimatorProblem,
    truth: dict[str, np.ndarray],
    filt: dict[str, np.ndarray],
    forecast: dict[str, np.ndarray],
) -> dict[str, Path]:
    """Create visual diagnostics."""

    import matplotlib.pyplot as plt

    paths: dict[str, Path] = {}
    t = np.arange(problem.steps + 1) * problem.dt
    ty = np.arange(problem.steps) * problem.dt
    X_true = truth["X_true"]
    Y = truth["Y"]
    xhat = filt["xhat"]
    xhat_minus = filt["xhat_minus"]
    P = filt["P"]
    P_minus = filt["P_minus"]
    innovation = filt["innovation"]
    L = filt["L"]

    # Plot states and measurements.
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(t, X_true[:, 0], label="true position")
    ax.scatter(ty, Y[:, 0], s=15, label="noisy measured position")
    ax.plot(ty, xhat[:, 0], label="estimated position after measurement")
    ax.plot(t, xhat_minus[:, 0], linestyle="--", label="forecasted position before measurement")
    ax.set_title("Linear state estimation: true, measured, estimated, and forecasted position")
    ax.set_xlabel("time")
    ax.set_ylabel("position")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    p = out_dir / f"{stem}_states.png"
    fig.savefig(p, dpi=160)
    plt.close(fig)
    paths["states_plot"] = p

    # Plot estimation errors with +/- 2 sigma bounds.
    fig, ax = plt.subplots(figsize=(11, 6))
    err = X_true[:problem.steps] - xhat
    for i, name in enumerate(problem.state_names):
        sigma = np.sqrt(np.maximum(P[:, i, i], 0.0))
        ax.plot(ty, err[:, i], label=f"{name} error")
        ax.plot(ty, 2.0 * sigma, linestyle="--", label=f"+2 sigma {name}")
        ax.plot(ty, -2.0 * sigma, linestyle="--", label=f"-2 sigma {name}")
    ax.set_title("Estimation error and posterior covariance bounds")
    ax.set_xlabel("time")
    ax.set_ylabel("true state - estimated state")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    p = out_dir / f"{stem}_errors.png"
    fig.savefig(p, dpi=160)
    plt.close(fig)
    paths["errors_plot"] = p

    # Covariance plot: prior/forecast variance versus posterior variance.
    fig, ax = plt.subplots(figsize=(11, 5.8))
    for i, name in enumerate(problem.state_names):
        ax.plot(t, P_minus[:, i, i], linestyle="--", label=f"forecast variance {name}")
        ax.plot(ty, P[:, i, i], label=f"posterior variance {name}")
    ax.set_title("Covariance behavior: forecast grows, measurement update shrinks")
    ax.set_xlabel("time")
    ax.set_ylabel("variance")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    p = out_dir / f"{stem}_covariance.png"
    fig.savefig(p, dpi=160)
    plt.close(fig)
    paths["covariance_plot"] = p

    # Innovation and gain.
    fig, ax = plt.subplots(figsize=(11, 5.8))
    ax.plot(ty, innovation[:, 0], label="innovation y - C xhat_minus")
    ax.plot(ty, L[:, 0, 0], label="gain on position state")
    ax.plot(ty, L[:, 1, 0], label="gain on velocity state")
    ax.set_title("Innovation and estimator gain")
    ax.set_xlabel("time")
    ax.set_ylabel("value")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    p = out_dir / f"{stem}_innovation_gain.png"
    fig.savefig(p, dpi=160)
    plt.close(fig)
    paths["innovation_gain_plot"] = p

    # Forecast beyond final measurement.
    tf = t[-1] + np.arange(forecast["forecast_x"].shape[0]) * problem.dt
    fig, ax = plt.subplots(figsize=(11, 5.8))
    ax.plot(ty, xhat[:, 0], label="estimated position with measurements")
    ax.plot(tf, forecast["forecast_x"][:, 0], linestyle="--", label="open forecast after measurements stop")
    sig = np.sqrt(np.maximum(forecast["forecast_P"][:, 0, 0], 0.0))
    ax.plot(tf, forecast["forecast_x"][:, 0] + 2.0 * sig, linestyle=":", label="forecast +2 sigma")
    ax.plot(tf, forecast["forecast_x"][:, 0] - 2.0 * sig, linestyle=":", label="forecast -2 sigma")
    ax.set_title("Forecasting after the final measurement")
    ax.set_xlabel("time")
    ax.set_ylabel("position")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    p = out_dir / f"{stem}_future_forecast.png"
    fig.savefig(p, dpi=160)
    plt.close(fig)
    paths["future_forecast_plot"] = p

    return paths


def run(steps: int, seed: int, out: str | Path, future_steps: int, log_steps: int) -> dict[str, Path]:
    """Run the full sandbox and return written file paths."""

    problem = default_problem(steps=steps)
    truth = simulate_truth(problem, seed=seed)
    filt = kalman_filter(problem, truth["Y"])
    forecast = forecast_from_last_estimate(problem, filt["xhat"][-1], filt["P"][-1], future_steps=future_steps)
    log_text = make_calculation_log(problem, truth, filt, forecast, max_steps=log_steps)
    return write_outputs(Path(out), problem, truth, filt, forecast, log_text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Section 1.4.2 linear optimal state estimation sandbox")
    parser.add_argument("--steps", type=int, default=70, help="number of measurement/update steps")
    parser.add_argument("--seed", type=int, default=7, help="random seed for synthetic process and measurement noise")
    parser.add_argument("--out", default="out/linear_state_estimation", help="output directory")
    parser.add_argument("--future-steps", type=int, default=24, help="forecast steps after measurements stop")
    parser.add_argument("--log-steps", type=int, default=8, help="number of detailed calculation steps written to log")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.steps < 2:
        raise SystemExit("--steps must be at least 2")
    if args.future_steps < 1:
        raise SystemExit("--future-steps must be at least 1")
    paths = run(args.steps, args.seed, args.out, args.future_steps, args.log_steps)
    print("Linear state estimation sandbox complete.")
    print(f"Output directory: {Path(args.out).resolve()}")
    for label, path in paths.items():
        print(f"  {label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
