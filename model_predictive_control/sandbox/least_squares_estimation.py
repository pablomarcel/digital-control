#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
least_squares_estimation.py

Sandbox for Rawlings/Mayne/Diehl, Section 1.4.3: Least Squares Estimation.

The section rewrites the linear state-estimation problem as a deterministic
least-squares optimization over the whole state sequence:

    minimize over x(0), ..., x(T):

        1/2 |x(0) - xbar(0)|^2_{P0^{-1}}
      + 1/2 sum_{k=0}^{T-1} |x(k+1) - A x(k) - B u(k)|^2_{Q^{-1}}
      + 1/2 sum_{k=0}^{T} |y(k) - C x(k)|^2_{R^{-1}}

The textbook writes the model without the known engineering input B u(k).
This script includes B u(k) because it is useful for control/MPC workflows.
Set B or u to zero to recover the compact textbook form.

What this script does
---------------------
1. Generates synthetic data from a noisy linear double-integrator model.
2. Solves the full batch least-squares problem by building the dense normal
   equations for the entire state trajectory.
3. Solves the same problem recursively using the forward-DP / recursive least
   squares equations. This is the same numerical recursion as the Kalman filter
   for the unconstrained linear-Gaussian case.
4. Writes a detailed calculation log showing the actual matrix arithmetic.
5. Writes JSON, CSV, and diagnostic plots.

Default output directory:
    out/least_squares_estimation

Run:
    python least_squares_estimation.py

Optional:
    python least_squares_estimation.py --steps 45 --seed 7 --out out/least_squares_estimation
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import argparse
import csv
import json

import numpy as np


@dataclass(frozen=True)
class LeastSquaresEstimationProblem:
    """Container for a linear least-squares state-estimation sandbox."""

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
        """Number of transitions. Measurements are generated at k=0..steps."""

        return int(self.U.shape[0])


def arr(value: Any) -> np.ndarray:
    """Return a float NumPy array."""

    return np.asarray(value, dtype=float)


def mat_to_str(M: np.ndarray, precision: int = 6) -> str:
    """Compact matrix/vector string for calculation logs."""

    return np.array2string(np.asarray(M, dtype=float), precision=precision, suppress_small=False)


def as_jsonable(value: Any) -> Any:
    """Convert NumPy-heavy structures to JSON-safe Python structures."""

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
    """Return W such that ||W r||^2 = r.T inv(cov) r."""

    info = np.linalg.inv(cov)
    L = np.linalg.cholesky(info)  # info = L L.T
    return L.T


def weighted_norm_sq(residual: np.ndarray, cov: np.ndarray) -> float:
    """Return residual.T inv(cov) residual as a scalar."""

    r = np.asarray(residual, dtype=float).reshape(-1)
    return float(r.T @ np.linalg.inv(cov) @ r)


def default_problem(steps: int = 45) -> LeastSquaresEstimationProblem:
    """Build a small double-integrator example with position measurements."""

    dt = 0.1
    A = arr([[1.0, dt], [0.0, 1.0]])
    B = arr([[0.5 * dt * dt], [dt]])
    C = arr([[1.0, 0.0]])

    # Q is the covariance/weight for the model mismatch residual:
    #   x(k+1) - A x(k) - B u(k)
    # It is full-rank so the least-squares weight Q^{-1} is well-defined.
    Q = arr([[0.0025, 0.0], [0.0, 0.0400]])

    # R is the measurement-noise covariance.
    R = arr([[0.09]])

    # Prior information on x(0): intentionally wrong and uncertain.
    xbar0 = arr([0.0, 0.0])
    P0 = arr([[9.0, 0.0], [0.0, 4.0]])

    # True initial state used only to generate synthetic data.
    x0_true = arr([2.5, -0.2])

    t = np.arange(steps) * dt
    U = (0.55 * np.sin(0.55 * t) - 0.20 * (t > 2.5)).reshape(-1, 1)

    return LeastSquaresEstimationProblem(
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
        state_names=["position", "velocity"],
        output_names=["measured_position"],
        input_names=["acceleration_command"],
    )


def simulate_truth(problem: LeastSquaresEstimationProblem, seed: int) -> dict[str, np.ndarray]:
    """Generate a repeatable true trajectory and noisy measurements."""

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


def build_dense_least_squares_system(
    problem: LeastSquaresEstimationProblem,
    Y: np.ndarray,
) -> dict[str, np.ndarray]:
    """Build E z = d for the weighted batch least-squares problem."""

    T = problem.steps
    nx, ny = problem.nx, problem.ny
    nvars = (T + 1) * nx
    nrows = nx + T * nx + (T + 1) * ny
    E = np.zeros((nrows, nvars))
    d = np.zeros(nrows)

    WP0 = sqrt_information(problem.P0)
    WQ = sqrt_information(problem.Q)
    WR = sqrt_information(problem.R)

    row = 0

    # Prior residual: x(0) - xbar0.
    E[row:row + nx, 0:nx] = WP0
    d[row:row + nx] = WP0 @ problem.xbar0
    row += nx

    # Process residuals: x(k+1) - A x(k) - B u(k).
    for k in range(T):
        c0 = k * nx
        c1 = (k + 1) * nx
        E[row:row + nx, c0:c0 + nx] = WQ @ (-problem.A)
        E[row:row + nx, c1:c1 + nx] = WQ
        d[row:row + nx] = WQ @ (problem.B @ problem.U[k])
        row += nx

    # Measurement residuals: C x(k) - y(k).
    for k in range(T + 1):
        c = k * nx
        E[row:row + ny, c:c + nx] = WR @ problem.C
        d[row:row + ny] = WR @ Y[k]
        row += ny

    assert row == nrows
    H = E.T @ E
    g = E.T @ d
    return {"E": E, "d": d, "H": H, "g": g}


def solve_batch_least_squares(
    problem: LeastSquaresEstimationProblem,
    Y: np.ndarray,
) -> dict[str, np.ndarray | float]:
    """Solve the full dense least-squares problem over x(0), ..., x(T)."""

    sys = build_dense_least_squares_system(problem, Y)
    E = sys["E"]
    d = sys["d"]
    H = sys["H"]
    g = sys["g"]
    z = np.linalg.solve(H, g)
    X = z.reshape(problem.steps + 1, problem.nx)
    residual = E @ z - d
    objective = 0.5 * float(residual.T @ residual)
    return {
        "X_batch": X,
        "z": z,
        "residual": residual,
        "objective": objective,
        "E": E,
        "d": d,
        "H": H,
        "g": g,
    }


def recursive_least_squares_forward_dp(
    problem: LeastSquaresEstimationProblem,
    Y: np.ndarray,
) -> dict[str, np.ndarray]:
    """Run the forward-DP recursive least-squares estimator.

    This updates an arrival cost at each sample. For linear unconstrained
    systems with quadratic penalties, it matches the batch least-squares
    minimizer for the filtered state at the current final time.
    """

    T = problem.steps
    nx, ny = problem.nx, problem.ny
    x_minus = np.zeros((T + 1, nx))
    x_plus = np.zeros((T + 1, nx))
    P_minus = np.zeros((T + 1, nx, nx))
    P_plus = np.zeros((T + 1, nx, nx))
    L = np.zeros((T + 1, nx, ny))
    S = np.zeros((T + 1, ny, ny))
    innovation = np.zeros((T + 1, ny))

    x_minus[0] = problem.xbar0
    P_minus[0] = problem.P0

    for k in range(T + 1):
        # Measurement least-squares update:
        # min_x 1/2 |x - x_minus|^2_{P_minus^{-1}} + 1/2 |y - Cx|^2_{R^{-1}}
        innovation[k] = Y[k] - problem.C @ x_minus[k]
        S[k] = problem.C @ P_minus[k] @ problem.C.T + problem.R
        L[k] = P_minus[k] @ problem.C.T @ np.linalg.inv(S[k])
        x_plus[k] = x_minus[k] + L[k] @ innovation[k]
        P_plus[k] = P_minus[k] - P_minus[k] @ problem.C.T @ np.linalg.inv(S[k]) @ problem.C @ P_minus[k]
        P_plus[k] = 0.5 * (P_plus[k] + P_plus[k].T)

        if k < T:
            # Arrival-cost propagation:
            # min_{x_k} V_k(x_k) + 1/2 |x_{k+1} - A x_k - B u_k|^2_{Q^{-1}}
            # gives V^-_{k+1}(x_{k+1}) centered at A xhat_k + B u_k.
            x_minus[k + 1] = problem.A @ x_plus[k] + problem.B @ problem.U[k]
            P_minus[k + 1] = problem.A @ P_plus[k] @ problem.A.T + problem.Q
            P_minus[k + 1] = 0.5 * (P_minus[k + 1] + P_minus[k + 1].T)

    return {
        "x_minus": x_minus,
        "x_plus": x_plus,
        "P_minus": P_minus,
        "P_plus": P_plus,
        "L": L,
        "S": S,
        "innovation": innovation,
    }


def objective_breakdown(
    problem: LeastSquaresEstimationProblem,
    X: np.ndarray,
    Y: np.ndarray,
) -> dict[str, Any]:
    """Compute prior, process, and measurement cost terms for a state sequence."""

    T = problem.steps
    prior_res = X[0] - problem.xbar0
    prior_cost = 0.5 * weighted_norm_sq(prior_res, problem.P0)

    process_costs = []
    process_residuals = []
    for k in range(T):
        r = X[k + 1] - problem.A @ X[k] - problem.B @ problem.U[k]
        process_residuals.append(r)
        process_costs.append(0.5 * weighted_norm_sq(r, problem.Q))

    measurement_costs = []
    measurement_residuals = []
    for k in range(T + 1):
        r = Y[k] - problem.C @ X[k]
        measurement_residuals.append(r)
        measurement_costs.append(0.5 * weighted_norm_sq(r, problem.R))

    return {
        "prior_residual": prior_res,
        "prior_cost": float(prior_cost),
        "process_residuals": np.asarray(process_residuals),
        "process_costs": np.asarray(process_costs),
        "measurement_residuals": np.asarray(measurement_residuals),
        "measurement_costs": np.asarray(measurement_costs),
        "process_cost_total": float(np.sum(process_costs)),
        "measurement_cost_total": float(np.sum(measurement_costs)),
        "total_cost": float(prior_cost + np.sum(process_costs) + np.sum(measurement_costs)),
    }


def make_calculation_log(
    problem: LeastSquaresEstimationProblem,
    truth: dict[str, np.ndarray],
    batch: dict[str, Any],
    rls: dict[str, np.ndarray],
    breakdown_batch: dict[str, Any],
    breakdown_rls: dict[str, Any],
    max_steps: int = 7,
) -> str:
    """Create a detailed calculation log for the least-squares estimator."""

    lines: list[str] = []
    T = problem.steps
    Y = truth["Y"]
    X_true = truth["X_true"]
    X_batch = batch["X_batch"]
    x_minus = rls["x_minus"]
    x_plus = rls["x_plus"]
    P_minus = rls["P_minus"]
    P_plus = rls["P_plus"]
    L = rls["L"]
    S = rls["S"]
    innovation = rls["innovation"]

    lines.append("Least Squares State Estimation Calculation Log")
    lines.append("Rawlings/Mayne/Diehl Section 1.4.3 sandbox")
    lines.append("")
    lines.append("Least-squares problem implemented")
    lines.append("  minimize over x(0), ..., x(T):")
    lines.append("    1/2 |x(0) - xbar(0)|^2_{P0^{-1}}")
    lines.append("  + 1/2 sum |x(k+1) - A x(k) - B u(k)|^2_{Q^{-1}}")
    lines.append("  + 1/2 sum |y(k) - C x(k)|^2_{R^{-1}}")
    lines.append("")
    lines.append("The textbook writes x(k+1) - A x(k). This script includes known input B u(k).")
    lines.append("")
    lines.append("Matrices")
    for name, M in [
        ("A", problem.A),
        ("B", problem.B),
        ("C", problem.C),
        ("Q", problem.Q),
        ("R", problem.R),
        ("xbar0", problem.xbar0),
        ("P0", problem.P0),
    ]:
        lines.append(f"{name} = {mat_to_str(M)}")

    lines.append("")
    lines.append("Batch dense least-squares construction")
    lines.append("  Weighted residual form: minimize 1/2 ||E z - d||^2")
    lines.append("  Decision vector z = [x(0); x(1); ...; x(T)]")
    lines.append(f"  T = {T}, nx = {problem.nx}, ny = {problem.ny}")
    lines.append(f"  E shape = {batch['E'].shape}")
    lines.append(f"  H = E.T E shape = {batch['H'].shape}")
    lines.append(f"  g = E.T d shape = {batch['g'].shape}")
    lines.append("  Dense normal equation solved: H z = g")
    lines.append(f"  batch objective = {batch['objective']:.12g}")
    lines.append("")
    lines.append("Cost breakdown for batch minimizer")
    lines.append(f"  prior cost      = {breakdown_batch['prior_cost']:.12g}")
    lines.append(f"  process cost    = {breakdown_batch['process_cost_total']:.12g}")
    lines.append(f"  measurement cost= {breakdown_batch['measurement_cost_total']:.12g}")
    lines.append(f"  total cost      = {breakdown_batch['total_cost']:.12g}")
    lines.append("")
    lines.append("Recursive forward-DP least-squares update used")
    lines.append("  Measurement combination:")
    lines.append("    innovation(k) = y(k) - C x_minus(k)")
    lines.append("    S(k)          = C P_minus(k) C.T + R")
    lines.append("    L(k)          = P_minus(k) C.T inv(S(k))")
    lines.append("    x_plus(k)     = x_minus(k) + L(k) innovation(k)")
    lines.append("    P_plus(k)     = P_minus(k) - P_minus(k) C.T inv(S(k)) C P_minus(k)")
    lines.append("  Arrival-cost propagation:")
    lines.append("    x_minus(k+1)  = A x_plus(k) + B u(k)")
    lines.append("    P_minus(k+1)  = A P_plus(k) A.T + Q")
    lines.append("")
    lines.append("Cost breakdown for recursive filtered sequence")
    lines.append(f"  prior cost      = {breakdown_rls['prior_cost']:.12g}")
    lines.append(f"  process cost    = {breakdown_rls['process_cost_total']:.12g}")
    lines.append(f"  measurement cost= {breakdown_rls['measurement_cost_total']:.12g}")
    lines.append(f"  total cost      = {breakdown_rls['total_cost']:.12g}")
    lines.append("")
    lines.append("Important warning")
    lines.append("  The batch solution uses all measurements y(0)...y(T) to estimate every state.")
    lines.append("  That means it is a smoothing/full-information estimate.")
    lines.append("  The recursive x_plus(k) is the filtered estimate using measurements only up to k.")
    lines.append("  The two are expected to match closely at the final state x(T), not at every past state.")
    lines.append("")
    lines.append("Final-state comparison")
    lines.append(f"  batch x(T)     = {mat_to_str(X_batch[-1])}")
    lines.append(f"  recursive x(T) = {mat_to_str(x_plus[-1])}")
    lines.append(f"  difference     = {mat_to_str(X_batch[-1] - x_plus[-1])}")
    lines.append(f"  norm diff      = {np.linalg.norm(X_batch[-1] - x_plus[-1]):.12g}")
    lines.append("")

    for k in range(min(max_steps, T + 1)):
        lines.append("-" * 78)
        lines.append(f"Step k = {k}")
        if k < T:
            lines.append(f"u({k}) = {mat_to_str(problem.U[k])}")
        lines.append(f"true x({k}) = {mat_to_str(X_true[k])}")
        lines.append(f"measurement y({k}) = {mat_to_str(Y[k])}")
        lines.append("")
        lines.append("Recursive measurement least-squares update")
        lines.append(f"x_minus({k}) = {mat_to_str(x_minus[k])}")
        lines.append(f"P_minus({k}) = {mat_to_str(P_minus[k])}")
        lines.append(f"innovation({k}) = y - C x_minus = {mat_to_str(innovation[k])}")
        lines.append(f"S({k}) = C P_minus C.T + R = {mat_to_str(S[k])}")
        lines.append(f"L({k}) = P_minus C.T inv(S) = {mat_to_str(L[k])}")
        lines.append(f"x_plus({k}) = x_minus + L innovation = {mat_to_str(x_plus[k])}")
        lines.append(f"P_plus({k}) = {mat_to_str(P_plus[k])}")
        lines.append(f"batch smoothed x({k}) = {mat_to_str(X_batch[k])}")
        lines.append(f"filtered error true - x_plus = {mat_to_str(X_true[k] - x_plus[k])}")
        lines.append(f"batch error true - x_batch = {mat_to_str(X_true[k] - X_batch[k])}")
        lines.append("")
        lines.append("Objective residuals at recursive filtered estimate")
        lines.append(f"measurement residual y-Cx = {mat_to_str(breakdown_rls['measurement_residuals'][k])}")
        lines.append(f"measurement cost contribution = {breakdown_rls['measurement_costs'][k]:.12g}")
        if k < T:
            lines.append(f"process residual x(k+1)-A x(k)-B u(k) = {mat_to_str(breakdown_rls['process_residuals'][k])}")
            lines.append(f"process cost contribution = {breakdown_rls['process_costs'][k]:.12g}")
            lines.append("")
            lines.append("Arrival-cost propagation")
            lines.append(f"x_minus({k+1}) = A x_plus({k}) + B u({k}) = {mat_to_str(x_minus[k+1])}")
            lines.append(f"P_minus({k+1}) = A P_plus({k}) A.T + Q = {mat_to_str(P_minus[k+1])}")
        lines.append("")

    lines.append("-" * 78)
    lines.append("Engineering interpretation")
    lines.append("  Least squares is asking for the state trajectory that best compromises between:")
    lines.append("    1. the initial prior guess,")
    lines.append("    2. the model x(k+1)=A x(k)+B u(k),")
    lines.append("    3. the noisy measurements y(k)=C x(k).")
    lines.append("  Q and R are weights. Small Q punishes model mismatch strongly. Small R punishes")
    lines.append("  measurement mismatch strongly. In the Gaussian case, these weights are covariance")
    lines.append("  matrices, and the least-squares solution matches optimal statistical estimation.")
    return "\n".join(lines) + "\n"


def write_outputs(
    out_dir: Path,
    problem: LeastSquaresEstimationProblem,
    truth: dict[str, np.ndarray],
    batch: dict[str, Any],
    rls: dict[str, np.ndarray],
    breakdown_batch: dict[str, Any],
    breakdown_rls: dict[str, Any],
    log_text: str,
) -> dict[str, Path]:
    """Write JSON, CSV, TXT, and plot outputs."""

    out_dir.mkdir(parents=True, exist_ok=True)
    stem = "least_squares_estimation"
    paths: dict[str, Path] = {}

    X_true = truth["X_true"]
    Y = truth["Y"]
    X_batch = batch["X_batch"]
    x_plus = rls["x_plus"]
    x_minus = rls["x_minus"]
    P_plus = rls["P_plus"]
    innovation = rls["innovation"]
    L = rls["L"]

    result = {
        "title": "Least Squares State Estimation - Section 1.4.3 Sandbox",
        "model": {
            "A": problem.A,
            "B": problem.B,
            "C": problem.C,
            "Q": problem.Q,
            "R": problem.R,
            "dt": problem.dt,
        },
        "prior": {"xbar0": problem.xbar0, "P0": problem.P0, "x0_true_for_synthetic_data": problem.x0_true},
        "state_names": problem.state_names,
        "output_names": problem.output_names,
        "input_names": problem.input_names,
        "time": np.arange(problem.steps + 1) * problem.dt,
        "U": problem.U,
        "Y": Y,
        "X_true": X_true,
        "X_batch_full_information": X_batch,
        "x_recursive_filtered": x_plus,
        "x_recursive_forecast_before_measurement": x_minus,
        "P_recursive_filtered": P_plus,
        "L_recursive_gain": L,
        "innovation": innovation,
        "batch_objective": batch["objective"],
        "batch_cost_breakdown": breakdown_batch,
        "recursive_filtered_sequence_cost_breakdown": breakdown_rls,
        "final_state_difference_batch_minus_recursive": X_batch[-1] - x_plus[-1],
        "final_state_difference_norm": float(np.linalg.norm(X_batch[-1] - x_plus[-1])),
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
        writer.writerow([
            "k", "time", "u_acceleration_command", "y_measured_position",
            "x_true_position", "x_true_velocity",
            "x_batch_position", "x_batch_velocity",
            "x_recursive_position", "x_recursive_velocity",
            "x_forecast_before_meas_position", "x_forecast_before_meas_velocity",
            "batch_error_position", "batch_error_velocity",
            "recursive_error_position", "recursive_error_velocity",
            "innovation", "gain_position", "gain_velocity",
            "P_recursive_pos_var", "P_recursive_vel_var",
            "batch_process_cost", "recursive_process_cost",
            "batch_measurement_cost", "recursive_measurement_cost",
        ])
        for k in range(problem.steps + 1):
            u = problem.U[k, 0] if k < problem.steps else ""
            batch_process = breakdown_batch["process_costs"][k] if k < problem.steps else ""
            rls_process = breakdown_rls["process_costs"][k] if k < problem.steps else ""
            writer.writerow([
                k, k * problem.dt, u, Y[k, 0],
                X_true[k, 0], X_true[k, 1],
                X_batch[k, 0], X_batch[k, 1],
                x_plus[k, 0], x_plus[k, 1],
                x_minus[k, 0], x_minus[k, 1],
                X_true[k, 0] - X_batch[k, 0], X_true[k, 1] - X_batch[k, 1],
                X_true[k, 0] - x_plus[k, 0], X_true[k, 1] - x_plus[k, 1],
                innovation[k, 0], L[k, 0, 0], L[k, 1, 0],
                P_plus[k, 0, 0], P_plus[k, 1, 1],
                batch_process, rls_process,
                breakdown_batch["measurement_costs"][k], breakdown_rls["measurement_costs"][k],
            ])
    paths["csv"] = csv_path

    paths.update(make_plots(out_dir, stem, problem, truth, batch, rls, breakdown_batch, breakdown_rls))
    return paths


def make_plots(
    out_dir: Path,
    stem: str,
    problem: LeastSquaresEstimationProblem,
    truth: dict[str, np.ndarray],
    batch: dict[str, Any],
    rls: dict[str, np.ndarray],
    breakdown_batch: dict[str, Any],
    breakdown_rls: dict[str, Any],
) -> dict[str, Path]:
    """Create visual diagnostics for least-squares estimation."""

    import matplotlib.pyplot as plt

    paths: dict[str, Path] = {}
    t = np.arange(problem.steps + 1) * problem.dt
    tu = np.arange(problem.steps) * problem.dt
    X_true = truth["X_true"]
    Y = truth["Y"]
    X_batch = batch["X_batch"]
    x_plus = rls["x_plus"]
    x_minus = rls["x_minus"]
    P_plus = rls["P_plus"]

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(t, X_true[:, 0], label="true position")
    ax.scatter(t, Y[:, 0], s=15, label="noisy measured position")
    ax.plot(t, X_batch[:, 0], label="batch LS position: uses all measurements")
    ax.plot(t, x_plus[:, 0], linestyle="--", label="recursive filtered position: uses data up to k")
    ax.plot(t, x_minus[:, 0], linestyle=":", label="recursive forecast before measurement")
    ax.set_title("Least-squares state estimation: position")
    ax.set_xlabel("time")
    ax.set_ylabel("position")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    p = out_dir / f"{stem}_position.png"
    fig.savefig(p, dpi=160)
    plt.close(fig)
    paths["position_plot"] = p

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(t, X_true[:, 1], label="true velocity")
    ax.plot(t, X_batch[:, 1], label="batch LS velocity")
    ax.plot(t, x_plus[:, 1], linestyle="--", label="recursive filtered velocity")
    ax.set_title("Least-squares state estimation: hidden velocity")
    ax.set_xlabel("time")
    ax.set_ylabel("velocity")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    p = out_dir / f"{stem}_velocity.png"
    fig.savefig(p, dpi=160)
    plt.close(fig)
    paths["velocity_plot"] = p

    fig, ax = plt.subplots(figsize=(11, 5.8))
    ax.plot(t, X_true[:, 0] - X_batch[:, 0], label="position error: batch LS")
    ax.plot(t, X_true[:, 0] - x_plus[:, 0], linestyle="--", label="position error: recursive filtered")
    ax.plot(t, X_true[:, 1] - X_batch[:, 1], label="velocity error: batch LS")
    ax.plot(t, X_true[:, 1] - x_plus[:, 1], linestyle="--", label="velocity error: recursive filtered")
    ax.set_title("Estimation errors: batch smoothing versus recursive filtering")
    ax.set_xlabel("time")
    ax.set_ylabel("true state - estimated state")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    p = out_dir / f"{stem}_errors.png"
    fig.savefig(p, dpi=160)
    plt.close(fig)
    paths["errors_plot"] = p

    fig, ax = plt.subplots(figsize=(11, 5.8))
    ax.plot(tu, breakdown_batch["process_costs"], label="batch process mismatch cost")
    ax.plot(tu, breakdown_rls["process_costs"], linestyle="--", label="recursive sequence process mismatch cost")
    ax.plot(t, breakdown_batch["measurement_costs"], label="batch measurement mismatch cost")
    ax.plot(t, breakdown_rls["measurement_costs"], linestyle="--", label="recursive sequence measurement mismatch cost")
    ax.set_title("Least-squares objective contributions")
    ax.set_xlabel("time")
    ax.set_ylabel("cost contribution")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    p = out_dir / f"{stem}_objective_contributions.png"
    fig.savefig(p, dpi=160)
    plt.close(fig)
    paths["objective_plot"] = p

    fig, ax = plt.subplots(figsize=(11, 5.8))
    ax.plot(t, np.abs(X_batch[:, 0] - x_plus[:, 0]), label="|batch - recursive| position")
    ax.plot(t, np.abs(X_batch[:, 1] - x_plus[:, 1]), label="|batch - recursive| velocity")
    ax.set_title("Batch full-information estimate versus recursive filtered estimate")
    ax.set_xlabel("time")
    ax.set_ylabel("absolute difference")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    p = out_dir / f"{stem}_batch_vs_recursive_difference.png"
    fig.savefig(p, dpi=160)
    plt.close(fig)
    paths["batch_recursive_difference_plot"] = p

    fig, ax = plt.subplots(figsize=(11, 5.8))
    for i, name in enumerate(problem.state_names):
        ax.plot(t, P_plus[:, i, i], label=f"recursive posterior variance {name}")
    ax.set_title("Recursive least-squares uncertainty carried by the arrival cost")
    ax.set_xlabel("time")
    ax.set_ylabel("variance")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    p = out_dir / f"{stem}_recursive_covariance.png"
    fig.savefig(p, dpi=160)
    plt.close(fig)
    paths["recursive_covariance_plot"] = p

    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Section 1.4.3 least-squares estimation sandbox")
    parser.add_argument("--steps", type=int, default=45, help="Number of model transitions. Measurements are steps+1.")
    parser.add_argument("--seed", type=int, default=11, help="Random seed for repeatable synthetic data")
    parser.add_argument("--out", type=str, default="out/least_squares_estimation", help="Output directory")
    parser.add_argument("--log-steps", type=int, default=7, help="Number of detailed steps to include in the text log")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    problem = default_problem(steps=args.steps)
    truth = simulate_truth(problem, seed=args.seed)
    batch = solve_batch_least_squares(problem, truth["Y"])
    rls = recursive_least_squares_forward_dp(problem, truth["Y"])
    breakdown_batch = objective_breakdown(problem, batch["X_batch"], truth["Y"])
    breakdown_rls = objective_breakdown(problem, rls["x_plus"], truth["Y"])
    log_text = make_calculation_log(problem, truth, batch, rls, breakdown_batch, breakdown_rls, max_steps=args.log_steps)
    paths = write_outputs(Path(args.out), problem, truth, batch, rls, breakdown_batch, breakdown_rls, log_text)

    print("Least-squares estimation sandbox complete.")
    for key, path in paths.items():
        print(f"  {key}: {path}")
    print(f"  final batch-recursive state difference norm: {np.linalg.norm(batch['X_batch'][-1] - rls['x_plus'][-1]):.6e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
