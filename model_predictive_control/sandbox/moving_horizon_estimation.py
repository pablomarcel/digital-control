#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
moving_horizon_estimation.py

Sandbox for Rawlings/Mayne/Diehl, Section 1.4.4: Moving Horizon Estimation.

MHE replaces the growing full-information least-squares problem with a sliding
window problem. At final time T, estimate only

    x(T-N), x(T-N+1), ..., x(T)

using only the recent measurements

    y(T-N), y(T-N+1), ..., y(T).

This script demonstrates two useful versions:

1. zero-prior MHE, close to the compact introductory cost in Section 1.4.4:

      1/2 sum |x(k+1) - A x(k) - B u(k)|^2_{Q^{-1}}
    + 1/2 sum |y(k) - C x(k)|^2_{R^{-1}}

2. arrival-prior MHE, which adds a prior at the left edge of the window:

      1/2 |x(T-N) - x_arr(T-N)|^2_{P_arr^{-1}} + window costs

The known engineering input B u(k) is included. Set B or u to zero to recover
the compact textbook form.

Default output directory:
    out/moving_horizon_estimation

Run:
    python moving_horizon_estimation.py

Optional:
    python moving_horizon_estimation.py --steps 55 --horizon 8 --seed 11 --out out/moving_horizon_estimation
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import argparse
import csv
import json
import time

import numpy as np


@dataclass(frozen=True)
class MHEProblem:
    A: np.ndarray
    B: np.ndarray
    C: np.ndarray
    Q: np.ndarray
    R: np.ndarray
    xbar0: np.ndarray
    P0: np.ndarray
    x0_true: np.ndarray
    U: np.ndarray
    dt: float
    horizon: int
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
    return np.asarray(value, dtype=float)


def mat_to_str(M: np.ndarray, precision: int = 6) -> str:
    return np.array2string(np.asarray(M, dtype=float), precision=precision, suppress_small=False)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    return value


def sqrt_information(cov: np.ndarray) -> np.ndarray:
    info = np.linalg.inv(cov)
    L = np.linalg.cholesky(info)  # info = L L.T
    return L.T


def weighted_norm_sq(residual: np.ndarray, cov: np.ndarray) -> float:
    r = np.asarray(residual, dtype=float).reshape(-1)
    return float(r.T @ np.linalg.inv(cov) @ r)


def default_problem(steps: int = 55, horizon: int = 8) -> MHEProblem:
    dt = 0.1
    A = arr([[1.0, dt], [0.0, 1.0]])
    B = arr([[0.5 * dt * dt], [dt]])
    C = arr([[1.0, 0.0]])

    # Q penalizes model mismatch x(k+1)-Ax(k)-Bu(k).
    # Smaller covariance => larger least-squares weight.
    Q = arr([[0.0025, 0.0], [0.0, 0.0400]])
    R = arr([[0.09]])

    # Intentionally poor prior so the window/arrival-cost behavior is visible.
    xbar0 = arr([0.0, 0.0])
    P0 = arr([[9.0, 0.0], [0.0, 4.0]])
    x0_true = arr([2.5, -0.2])

    t = np.arange(steps) * dt
    U = (0.60 * np.sin(0.50 * t) - 0.25 * (t > 2.8) + 0.18 * (t > 4.2)).reshape(-1, 1)

    return MHEProblem(
        A=A,
        B=B,
        C=C,
        Q=Q,
        R=R,
        xbar0=xbar0,
        P0=P0,
        x0_true=x0_true,
        U=U,
        dt=dt,
        horizon=horizon,
        state_names=["position", "velocity"],
        output_names=["measured_position"],
        input_names=["acceleration_command"],
    )


def simulate_truth(problem: MHEProblem, seed: int) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    T = problem.steps
    X_true = np.zeros((T + 1, problem.nx))
    Y = np.zeros((T + 1, problem.ny))
    W = np.zeros((T, problem.nx))
    V = np.zeros((T + 1, problem.ny))
    X_true[0] = problem.x0_true

    for k in range(T + 1):
        V[k] = rng.multivariate_normal(np.zeros(problem.ny), problem.R)
        Y[k] = problem.C @ X_true[k] + V[k]
        if k < T:
            W[k] = rng.multivariate_normal(np.zeros(problem.nx), problem.Q)
            X_true[k + 1] = problem.A @ X_true[k] + problem.B @ problem.U[k] + W[k]
    return {"X_true": X_true, "Y": Y, "W": W, "V": V}


def recursive_arrival_priors(problem: MHEProblem, Y: np.ndarray) -> dict[str, np.ndarray]:
    """Kalman/RLS recursion used only to supply an arrival prior for MHE."""
    T = problem.steps
    nx, ny = problem.nx, problem.ny
    x_minus = np.zeros((T + 1, nx))
    x_plus = np.zeros((T + 1, nx))
    P_minus = np.zeros((T + 1, nx, nx))
    P_plus = np.zeros((T + 1, nx, nx))
    L = np.zeros((T + 1, nx, ny))
    innovation = np.zeros((T + 1, ny))

    x_minus[0] = problem.xbar0
    P_minus[0] = problem.P0
    for k in range(T + 1):
        innovation[k] = Y[k] - problem.C @ x_minus[k]
        S = problem.C @ P_minus[k] @ problem.C.T + problem.R
        L[k] = P_minus[k] @ problem.C.T @ np.linalg.inv(S)
        x_plus[k] = x_minus[k] + L[k] @ innovation[k]
        P_plus[k] = P_minus[k] - L[k] @ problem.C @ P_minus[k]
        P_plus[k] = 0.5 * (P_plus[k] + P_plus[k].T)
        if k < T:
            x_minus[k + 1] = problem.A @ x_plus[k] + problem.B @ problem.U[k]
            P_minus[k + 1] = problem.A @ P_plus[k] @ problem.A.T + problem.Q
            P_minus[k + 1] = 0.5 * (P_minus[k + 1] + P_minus[k + 1].T)
    return {"x_minus": x_minus, "x_plus": x_plus, "P_minus": P_minus, "P_plus": P_plus, "L": L, "innovation": innovation}


def build_window_system(
    problem: MHEProblem,
    Y: np.ndarray,
    start: int,
    end: int,
    prior_mean: np.ndarray | None,
    prior_cov: np.ndarray | None,
) -> dict[str, np.ndarray]:
    """Build weighted residual E z = d for a window x(start)..x(end)."""
    nx, ny = problem.nx, problem.ny
    Lwin = end - start
    nstates = Lwin + 1
    prior_rows = nx if prior_mean is not None and prior_cov is not None else 0
    nrows = prior_rows + Lwin * nx + nstates * ny
    nvars = nstates * nx
    E = np.zeros((nrows, nvars))
    d = np.zeros(nrows)
    row = 0

    if prior_rows:
        WP = sqrt_information(prior_cov)
        E[row:row + nx, 0:nx] = WP
        d[row:row + nx] = WP @ prior_mean
        row += nx

    WQ = sqrt_information(problem.Q)
    for k in range(start, end):
        local = k - start
        c0 = local * nx
        c1 = (local + 1) * nx
        E[row:row + nx, c0:c0 + nx] = WQ @ (-problem.A)
        E[row:row + nx, c1:c1 + nx] = WQ
        d[row:row + nx] = WQ @ (problem.B @ problem.U[k])
        row += nx

    WR = sqrt_information(problem.R)
    for k in range(start, end + 1):
        local = k - start
        c = local * nx
        E[row:row + ny, c:c + nx] = WR @ problem.C
        d[row:row + ny] = WR @ Y[k]
        row += ny

    H = E.T @ E
    g = E.T @ d
    return {"E": E, "d": d, "H": H, "g": g}


def solve_window(
    problem: MHEProblem,
    Y: np.ndarray,
    start: int,
    end: int,
    prior_mean: np.ndarray | None = None,
    prior_cov: np.ndarray | None = None,
) -> dict[str, Any]:
    sys = build_window_system(problem, Y, start, end, prior_mean, prior_cov)
    tic = time.perf_counter()
    z = np.linalg.solve(sys["H"], sys["g"])
    solve_seconds = time.perf_counter() - tic
    X = z.reshape(end - start + 1, problem.nx)
    residual = sys["E"] @ z - sys["d"]
    objective = 0.5 * float(residual.T @ residual)
    bd = objective_breakdown_window(problem, X, Y, start, end, prior_mean, prior_cov)
    return {**sys, "z": z, "X": X, "residual": residual, "objective": objective, "start": start, "end": end, "solve_seconds": solve_seconds, "breakdown": bd}


def objective_breakdown_window(
    problem: MHEProblem,
    X: np.ndarray,
    Y: np.ndarray,
    start: int,
    end: int,
    prior_mean: np.ndarray | None,
    prior_cov: np.ndarray | None,
) -> dict[str, Any]:
    prior_cost = 0.0
    prior_residual = np.zeros(problem.nx)
    if prior_mean is not None and prior_cov is not None:
        prior_residual = X[0] - prior_mean
        prior_cost = 0.5 * weighted_norm_sq(prior_residual, prior_cov)

    process_costs = []
    process_residuals = []
    for k in range(start, end):
        local = k - start
        r = X[local + 1] - problem.A @ X[local] - problem.B @ problem.U[k]
        process_residuals.append(r)
        process_costs.append(0.5 * weighted_norm_sq(r, problem.Q))

    measurement_costs = []
    measurement_residuals = []
    for k in range(start, end + 1):
        local = k - start
        r = Y[k] - problem.C @ X[local]
        measurement_residuals.append(r)
        measurement_costs.append(0.5 * weighted_norm_sq(r, problem.R))

    return {
        "prior_residual": prior_residual,
        "prior_cost": float(prior_cost),
        "process_residuals": np.asarray(process_residuals),
        "process_costs": np.asarray(process_costs),
        "measurement_residuals": np.asarray(measurement_residuals),
        "measurement_costs": np.asarray(measurement_costs),
        "process_cost_total": float(np.sum(process_costs)),
        "measurement_cost_total": float(np.sum(measurement_costs)),
        "total_cost": float(prior_cost + np.sum(process_costs) + np.sum(measurement_costs)),
    }


def run_mhe(problem: MHEProblem, Y: np.ndarray) -> dict[str, Any]:
    T = problem.steps
    N = problem.horizon
    priors = recursive_arrival_priors(problem, Y)
    X_full_current = np.zeros((T + 1, problem.nx))
    X_mhe_zero = np.zeros((T + 1, problem.nx))
    X_mhe_arrival = np.zeros((T + 1, problem.nx))
    objectives_full = np.zeros(T + 1)
    objectives_zero = np.zeros(T + 1)
    objectives_arrival = np.zeros(T + 1)
    rows_full = np.zeros(T + 1, dtype=int)
    rows_mhe = np.zeros(T + 1, dtype=int)
    vars_full = np.zeros(T + 1, dtype=int)
    vars_mhe = np.zeros(T + 1, dtype=int)
    solve_time_full = np.zeros(T + 1)
    solve_time_zero = np.zeros(T + 1)
    solve_time_arrival = np.zeros(T + 1)
    starts = np.zeros(T + 1, dtype=int)
    snapshots: dict[int, dict[str, Any]] = {}

    snapshot_times = sorted(set([0, min(3, T), min(N, T), min(N + 4, T), min(2 * N, T), T]))

    for end in range(T + 1):
        # Full information estimate at current time end.
        full = solve_window(problem, Y, 0, end, problem.xbar0, problem.P0)
        X_full_current[end] = full["X"][-1]
        objectives_full[end] = full["objective"]
        rows_full[end] = full["E"].shape[0]
        vars_full[end] = full["E"].shape[1]
        solve_time_full[end] = full["solve_seconds"]

        start = max(0, end - N)
        starts[end] = start

        # Zero-prior MHE: while window is filling, include initial prior to avoid
        # underdetermined early problems. Once full, drop the early data completely.
        if start == 0:
            zero_prior_mean = problem.xbar0
            zero_prior_cov = problem.P0
        else:
            zero_prior_mean = None
            zero_prior_cov = None
        zero = solve_window(problem, Y, start, end, zero_prior_mean, zero_prior_cov)
        X_mhe_zero[end] = zero["X"][-1]
        objectives_zero[end] = zero["objective"]
        rows_mhe[end] = zero["E"].shape[0]
        vars_mhe[end] = zero["E"].shape[1]
        solve_time_zero[end] = zero["solve_seconds"]

        # Arrival-prior MHE: summarize old data with x_minus/P_minus at left edge.
        arrival = solve_window(problem, Y, start, end, priors["x_minus"][start], priors["P_minus"][start])
        X_mhe_arrival[end] = arrival["X"][-1]
        objectives_arrival[end] = arrival["objective"]
        solve_time_arrival[end] = arrival["solve_seconds"]

        if end in snapshot_times:
            snapshots[end] = {"full": full, "zero": zero, "arrival": arrival}

    return {
        "priors": priors,
        "X_full_current": X_full_current,
        "X_mhe_zero": X_mhe_zero,
        "X_mhe_arrival": X_mhe_arrival,
        "objectives_full": objectives_full,
        "objectives_zero": objectives_zero,
        "objectives_arrival": objectives_arrival,
        "rows_full": rows_full,
        "rows_mhe": rows_mhe,
        "vars_full": vars_full,
        "vars_mhe": vars_mhe,
        "solve_time_full": solve_time_full,
        "solve_time_zero": solve_time_zero,
        "solve_time_arrival": solve_time_arrival,
        "starts": starts,
        "snapshots": snapshots,
    }


def make_calculation_log(problem: MHEProblem, truth: dict[str, np.ndarray], result: dict[str, Any]) -> str:
    lines: list[str] = []
    T = problem.steps
    N = problem.horizon
    Y = truth["Y"]
    X_true = truth["X_true"]
    X_full = result["X_full_current"]
    X_zero = result["X_mhe_zero"]
    X_arrival = result["X_mhe_arrival"]
    starts = result["starts"]

    lines.append("Moving Horizon Estimation Calculation Log")
    lines.append("Rawlings/Mayne/Diehl Section 1.4.4 sandbox")
    lines.append("")
    lines.append("MHE idea implemented")
    lines.append("  At time T, estimate x(T-N), ..., x(T) using only y(T-N), ..., y(T).")
    lines.append("  Full-information estimation keeps growing from y(0), ..., y(T).")
    lines.append("  MHE keeps the optimization size bounded once T > N.")
    lines.append("")
    lines.append("Zero-prior MHE objective after the window is full")
    lines.append("  minimize over x(T-N), ..., x(T):")
    lines.append("    1/2 sum_{k=T-N}^{T-1} |x(k+1)-A x(k)-B u(k)|^2_{Q^{-1}}")
    lines.append("  + 1/2 sum_{k=T-N}^{T}   |y(k)-C x(k)|^2_{R^{-1}}")
    lines.append("")
    lines.append("Arrival-prior MHE objective")
    lines.append("  Adds 1/2 |x(T-N)-x_arr(T-N)|^2_{P_arr^{-1}} to summarize old data.")
    lines.append("  The arrival prior in this sandbox is generated by the recursive LS/Kalman update.")
    lines.append("")
    lines.append("Matrices")
    for name, M in [("A", problem.A), ("B", problem.B), ("C", problem.C), ("Q", problem.Q), ("R", problem.R), ("xbar0", problem.xbar0), ("P0", problem.P0)]:
        lines.append(f"{name} = {mat_to_str(M)}")
    lines.append(f"N = moving horizon length = {N}")
    lines.append(f"T_final = {T}")
    lines.append("")
    lines.append("Final-time comparison")
    lines.append(f"  true x(T)              = {mat_to_str(X_true[-1])}")
    lines.append(f"  full-information x(T)  = {mat_to_str(X_full[-1])}")
    lines.append(f"  zero-prior MHE x(T)    = {mat_to_str(X_zero[-1])}")
    lines.append(f"  arrival-prior MHE x(T) = {mat_to_str(X_arrival[-1])}")
    lines.append(f"  |full - zero|          = {np.linalg.norm(X_full[-1] - X_zero[-1]):.12g}")
    lines.append(f"  |full - arrival|       = {np.linalg.norm(X_full[-1] - X_arrival[-1]):.12g}")
    lines.append(f"  |true - arrival|       = {np.linalg.norm(X_true[-1] - X_arrival[-1]):.12g}")
    lines.append("")
    lines.append("Problem-size comparison at final time")
    lines.append(f"  full information variables = {result['vars_full'][-1]} ; rows = {result['rows_full'][-1]}")
    lines.append(f"  MHE variables              = {result['vars_mhe'][-1]} ; rows = {result['rows_mhe'][-1]}")
    lines.append("  This is the computational point of MHE: full-information grows; MHE saturates.")
    lines.append("")

    for end, pack in result["snapshots"].items():
        start = int(starts[end])
        lines.append("-" * 78)
        lines.append(f"Current time T = {end}, window start = {start}, samples in window = {end - start + 1}")
        lines.append(f"time interval = [{start * problem.dt:.3f}, {end * problem.dt:.3f}] seconds")
        lines.append(f"measurement y(T) = {mat_to_str(Y[end])}")
        lines.append(f"true x(T)       = {mat_to_str(X_true[end])}")
        lines.append("")
        for label in ["full", "zero", "arrival"]:
            sol = pack[label]
            bd = sol["breakdown"]
            Xw = sol["X"]
            lines.append(f"{label.upper()} solution")
            lines.append(f"  estimated left-edge x({sol['start']}) = {mat_to_str(Xw[0])}")
            lines.append(f"  estimated current  x({sol['end']}) = {mat_to_str(Xw[-1])}")
            lines.append(f"  E shape = {sol['E'].shape}; H shape = {sol['H'].shape}; g shape = {sol['g'].shape}")
            lines.append(f"  objective = {sol['objective']:.12g}")
            lines.append(f"  prior cost       = {bd['prior_cost']:.12g}")
            lines.append(f"  process cost     = {bd['process_cost_total']:.12g}")
            lines.append(f"  measurement cost = {bd['measurement_cost_total']:.12g}")
            lines.append(f"  error true-current minus estimate = {mat_to_str(X_true[end] - Xw[-1])}")
            if sol["end"] > sol["start"]:
                lines.append(f"  first process residual in window = {mat_to_str(bd['process_residuals'][0])}")
            lines.append(f"  first measurement residual in window = {mat_to_str(bd['measurement_residuals'][0])}")
            lines.append("")

    lines.append("-" * 78)
    lines.append("Engineering interpretation")
    lines.append("  Full information estimation uses all data from startup. Accurate, but the matrix grows every sample.")
    lines.append("  Moving horizon estimation throws away old raw measurements and solves a fixed-size problem.")
    lines.append("  Zero-prior MHE literally forgets old data once it leaves the window.")
    lines.append("  Arrival-prior MHE keeps a compressed memory of old data at the left edge of the window.")
    lines.append("  This is the estimator-side cousin of MPC: slide a window, optimize, use the current estimate, repeat.")
    return "\n".join(lines) + "\n"


def write_outputs(out_dir: Path, problem: MHEProblem, truth: dict[str, np.ndarray], result: dict[str, Any], log_text: str) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = "moving_horizon_estimation"
    paths: dict[str, Path] = {}
    T = problem.steps
    time_grid = np.arange(T + 1) * problem.dt
    X_true = truth["X_true"]
    Y = truth["Y"]
    X_full = result["X_full_current"]
    X_zero = result["X_mhe_zero"]
    X_arrival = result["X_mhe_arrival"]

    log_path = out_dir / f"{stem}_calculation_log.txt"
    log_path.write_text(log_text, encoding="utf-8")
    paths["calculation_log"] = log_path

    results_path = out_dir / f"{stem}_results.json"
    payload = {
        "title": "Moving Horizon Estimation sandbox",
        "section": "Rawlings/Mayne/Diehl Section 1.4.4",
        "dt": problem.dt,
        "steps": problem.steps,
        "horizon": problem.horizon,
        "A": problem.A,
        "B": problem.B,
        "C": problem.C,
        "Q": problem.Q,
        "R": problem.R,
        "xbar0": problem.xbar0,
        "P0": problem.P0,
        "time": time_grid,
        "X_true": X_true,
        "Y": Y,
        "U": problem.U,
        "X_full_current": X_full,
        "X_mhe_zero": X_zero,
        "X_mhe_arrival": X_arrival,
        "objectives_full": result["objectives_full"],
        "objectives_zero": result["objectives_zero"],
        "objectives_arrival": result["objectives_arrival"],
        "window_starts": result["starts"],
        "vars_full": result["vars_full"],
        "vars_mhe": result["vars_mhe"],
        "rows_full": result["rows_full"],
        "rows_mhe": result["rows_mhe"],
    }
    results_path.write_text(json.dumps(as_jsonable(payload), indent=2), encoding="utf-8")
    paths["results_json"] = results_path

    csv_path = out_dir / f"{stem}_timeseries.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "time", "true_position", "true_velocity", "measurement_position",
            "full_position", "full_velocity", "mhe_zero_position", "mhe_zero_velocity",
            "mhe_arrival_position", "mhe_arrival_velocity", "window_start",
            "objective_full", "objective_zero", "objective_arrival", "vars_full", "vars_mhe",
        ])
        for k in range(T + 1):
            writer.writerow([
                time_grid[k], X_true[k, 0], X_true[k, 1], Y[k, 0],
                X_full[k, 0], X_full[k, 1], X_zero[k, 0], X_zero[k, 1],
                X_arrival[k, 0], X_arrival[k, 1], result["starts"][k],
                result["objectives_full"][k], result["objectives_zero"][k], result["objectives_arrival"][k],
                result["vars_full"][k], result["vars_mhe"][k],
            ])
    paths["timeseries_csv"] = csv_path

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(time_grid, X_true[:, 0], label="true position")
    ax.scatter(time_grid, Y[:, 0], s=18, label="noisy measured position")
    ax.plot(time_grid, X_full[:, 0], label="full-information current estimate")
    ax.plot(time_grid, X_zero[:, 0], linestyle="--", label="zero-prior MHE position")
    ax.plot(time_grid, X_arrival[:, 0], linestyle=":", label="arrival-prior MHE position")
    ax.set_title("Moving horizon estimation: position")
    ax.set_xlabel("time")
    ax.set_ylabel("position")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path = out_dir / f"{stem}_position.png"
    fig.savefig(path, dpi=160)
    paths["position_plot"] = path
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.plot(time_grid, X_true[:, 1], label="true velocity")
    ax.plot(time_grid, X_full[:, 1], label="full-information velocity")
    ax.plot(time_grid, X_zero[:, 1], linestyle="--", label="zero-prior MHE velocity")
    ax.plot(time_grid, X_arrival[:, 1], linestyle=":", label="arrival-prior MHE velocity")
    ax.set_title("Moving horizon estimation: hidden velocity")
    ax.set_xlabel("time")
    ax.set_ylabel("velocity")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path = out_dir / f"{stem}_velocity.png"
    fig.savefig(path, dpi=160)
    paths["velocity_plot"] = path
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.plot(time_grid, np.linalg.norm(X_true - X_full, axis=1), label="||true - full information||")
    ax.plot(time_grid, np.linalg.norm(X_true - X_zero, axis=1), label="||true - zero-prior MHE||")
    ax.plot(time_grid, np.linalg.norm(X_true - X_arrival, axis=1), label="||true - arrival-prior MHE||")
    ax.set_title("Current-state estimation error")
    ax.set_xlabel("time")
    ax.set_ylabel("2-norm error")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path = out_dir / f"{stem}_errors.png"
    fig.savefig(path, dpi=160)
    paths["errors_plot"] = path
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.plot(time_grid, result["objectives_full"], label="full-information objective")
    ax.plot(time_grid, result["objectives_zero"], label="zero-prior MHE objective")
    ax.plot(time_grid, result["objectives_arrival"], label="arrival-prior MHE objective")
    ax.set_title("Objective value versus time")
    ax.set_xlabel("time")
    ax.set_ylabel("least-squares objective")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path = out_dir / f"{stem}_objectives.png"
    fig.savefig(path, dpi=160)
    paths["objectives_plot"] = path
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.step(time_grid, result["starts"], where="post", label="MHE window start index")
    ax.plot(time_grid, np.arange(T + 1), linestyle="--", label="current time index T")
    ax.set_title("Sliding window: old measurements are dropped")
    ax.set_xlabel("time")
    ax.set_ylabel("sample index")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path = out_dir / f"{stem}_window_indices.png"
    fig.savefig(path, dpi=160)
    paths["window_indices_plot"] = path
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.plot(time_grid, result["vars_full"], label="full-information decision variables")
    ax.plot(time_grid, result["vars_mhe"], label="MHE decision variables")
    ax.plot(time_grid, result["rows_full"], linestyle="--", label="full-information residual rows")
    ax.plot(time_grid, result["rows_mhe"], linestyle="--", label="MHE residual rows")
    ax.set_title("Optimization size: full information grows, MHE saturates")
    ax.set_xlabel("time")
    ax.set_ylabel("count")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path = out_dir / f"{stem}_problem_size.png"
    fig.savefig(path, dpi=160)
    paths["problem_size_plot"] = path
    plt.close(fig)

    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a moving-horizon-estimation sandbox.")
    parser.add_argument("--steps", type=int, default=55, help="Number of simulated transitions")
    parser.add_argument("--horizon", type=int, default=8, help="MHE window length N")
    parser.add_argument("--seed", type=int, default=11, help="Random seed for synthetic data")
    parser.add_argument("--out", type=str, default="out/moving_horizon_estimation", help="Output directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    problem = default_problem(steps=args.steps, horizon=args.horizon)
    truth = simulate_truth(problem, seed=args.seed)
    result = run_mhe(problem, truth["Y"])
    log_text = make_calculation_log(problem, truth, result)
    paths = write_outputs(Path(args.out), problem, truth, result, log_text)
    print("Moving horizon estimation run complete.")
    for key, path in paths.items():
        print(f"{key}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
