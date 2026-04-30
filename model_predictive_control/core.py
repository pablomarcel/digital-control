#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Core numerical routines for discrete-time model predictive control.

The module intentionally starts with a transparent SciPy-based linear MPC
implementation. It is meant for learning, experimentation, and automotive
control prototypes before moving to dedicated production-grade solvers.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import minimize

try:  # Import shim for direct script execution.
    from .utils import (
        InputError,
        as_array,
        as_square_matrix,
        broadcast_reference,
        matrix_weight,
        vector_or_default,
    )
except ImportError:  # pragma: no cover
    from utils import (  # type: ignore
        InputError,
        as_array,
        as_square_matrix,
        broadcast_reference,
        matrix_weight,
        vector_or_default,
    )


@dataclass
class LinearMPCProblem:
    """Normalized finite-horizon linear MPC problem data."""

    A: np.ndarray
    B: np.ndarray
    x0: np.ndarray
    horizon: int
    steps: int
    Q: np.ndarray
    R: np.ndarray
    P: np.ndarray
    Rd: np.ndarray
    x_ref: np.ndarray
    u_ref: np.ndarray
    d: np.ndarray
    x_min: np.ndarray | None
    x_max: np.ndarray | None
    u_min: np.ndarray | None
    u_max: np.ndarray | None
    du_min: np.ndarray | None
    du_max: np.ndarray | None
    A_sequence: np.ndarray | None = None
    B_sequence: np.ndarray | None = None
    dt: float = 1.0
    state_names: list[str] | None = None
    input_names: list[str] | None = None

    @property
    def nx(self) -> int:
        return int(self.A.shape[0])

    @property
    def nu(self) -> int:
        return int(self.B.shape[1])


def parse_problem(spec: dict[str, Any]) -> LinearMPCProblem:
    """Parse a dictionary into a normalized linear MPC problem."""

    plant = str(spec.get("plant", "linear_state_space")).lower()
    if plant in {"thermal_cooling_4state_demo", "automotive_thermal_cooling_demo"}:
        spec = build_thermal_cooling_spec(spec)

    model = spec.get("model", spec)
    if "A" not in model or "B" not in model:
        raise InputError("MPC input requires model.A and model.B matrices")

    A = as_square_matrix(model["A"], "model.A")
    B = as_array(model["B"], "model.B", ndim=2)
    if B.shape[0] != A.shape[0]:
        raise InputError(f"model.B rows must match model.A size; got A {A.shape}, B {B.shape}")

    nx = A.shape[0]
    nu = B.shape[1]
    x0 = as_array(spec.get("x0", np.zeros(nx)), "x0", ndim=1)
    if x0.size != nx:
        raise InputError(f"x0 must have length {nx}; got {x0.size}")

    horizon = int(spec.get("horizon", 10))
    steps = int(spec.get("steps", 50))
    if horizon < 1 or steps < 1:
        raise InputError("horizon and steps must be positive integers")

    weights = spec.get("weights", {})
    Q = matrix_weight(weights.get("Q", spec.get("Q")), nx, "Q", default_diag=1.0)
    R = matrix_weight(weights.get("R", spec.get("R")), nu, "R", default_diag=0.05)
    P = matrix_weight(weights.get("P", spec.get("P")), nx, "P", default_diag=1.0)
    Rd = matrix_weight(weights.get("Rd", spec.get("Rd")), nu, "Rd", default_diag=0.0)

    x_ref = broadcast_reference(spec.get("x_ref", spec.get("reference")), steps + horizon + 1, nx, "x_ref")
    u_ref = broadcast_reference(spec.get("u_ref"), steps + horizon, nu, "u_ref")
    d = broadcast_reference(model.get("d", spec.get("d")), steps + horizon, nx, "d")

    constraints = spec.get("constraints", {})
    x_min = _optional_bound(constraints.get("x_min", spec.get("x_min")), nx, "x_min")
    x_max = _optional_bound(constraints.get("x_max", spec.get("x_max")), nx, "x_max")
    u_min = _optional_bound(constraints.get("u_min", spec.get("u_min")), nu, "u_min")
    u_max = _optional_bound(constraints.get("u_max", spec.get("u_max")), nu, "u_max")
    du_min = _optional_bound(constraints.get("du_min", spec.get("du_min")), nu, "du_min")
    du_max = _optional_bound(constraints.get("du_max", spec.get("du_max")), nu, "du_max")

    A_sequence = _optional_matrix_sequence(model.get("A_sequence", spec.get("A_sequence")), steps + horizon, nx, nx, "A_sequence")
    B_sequence = _optional_matrix_sequence(model.get("B_sequence", spec.get("B_sequence")), steps + horizon, nx, nu, "B_sequence")

    return LinearMPCProblem(
        A=A,
        B=B,
        x0=x0,
        horizon=horizon,
        steps=steps,
        Q=Q,
        R=R,
        P=P,
        Rd=Rd,
        x_ref=x_ref,
        u_ref=u_ref,
        d=d,
        x_min=x_min,
        x_max=x_max,
        u_min=u_min,
        u_max=u_max,
        du_min=du_min,
        du_max=du_max,
        A_sequence=A_sequence,
        B_sequence=B_sequence,
        dt=float(spec.get("dt", model.get("dt", 1.0))),
        state_names=list(spec.get("state_names", [f"x{i + 1}" for i in range(nx)])),
        input_names=list(spec.get("input_names", [f"u{i + 1}" for i in range(nu)])),
    )


def _optional_bound(value: Any, size: int, name: str) -> np.ndarray | None:
    if value is None:
        return None
    return vector_or_default(value, 0.0, size, name)


def _optional_matrix_sequence(value: Any, count: int, rows: int, cols: int, name: str) -> np.ndarray | None:
    if value is None:
        return None
    arr = np.asarray(value, dtype=float)
    if arr.ndim != 3 or arr.shape[1:] != (rows, cols):
        raise InputError(f"{name} must have shape (k, {rows}, {cols}); got {arr.shape}")
    if arr.shape[0] >= count:
        return arr[:count].copy()
    tail = np.repeat(arr[-1:, :, :].copy(), count - arr.shape[0], axis=0)
    return np.concatenate([arr, tail], axis=0)


def get_AB(problem: LinearMPCProblem, index: int) -> tuple[np.ndarray, np.ndarray]:
    """Return the A and B matrices at a simulation or prediction index."""

    A = problem.A_sequence[index] if problem.A_sequence is not None else problem.A
    B = problem.B_sequence[index] if problem.B_sequence is not None else problem.B
    return A, B


def rollout(problem: LinearMPCProblem, x_start: np.ndarray, U: np.ndarray, time_index: int) -> np.ndarray:
    """Roll the model forward for one candidate input sequence."""

    X = np.zeros((problem.horizon + 1, problem.nx))
    X[0] = x_start
    for k in range(problem.horizon):
        A, B = get_AB(problem, time_index + k)
        X[k + 1] = A @ X[k] + B @ U[k] + problem.d[time_index + k]
    return X


def horizon_cost(problem: LinearMPCProblem, x_start: np.ndarray, U_flat: np.ndarray, time_index: int, u_prev: np.ndarray) -> float:
    """Evaluate the finite-horizon quadratic MPC objective."""

    U = U_flat.reshape(problem.horizon, problem.nu)
    X = rollout(problem, x_start, U, time_index)
    cost = 0.0
    prev = u_prev
    for k in range(problem.horizon):
        x_err = X[k] - problem.x_ref[time_index + k]
        u_err = U[k] - problem.u_ref[time_index + k]
        du = U[k] - prev
        cost += float(x_err.T @ problem.Q @ x_err)
        cost += float(u_err.T @ problem.R @ u_err)
        cost += float(du.T @ problem.Rd @ du)
        prev = U[k]
    x_terminal = X[-1] - problem.x_ref[time_index + problem.horizon]
    cost += float(x_terminal.T @ problem.P @ x_terminal)
    return cost


def solve_open_loop(problem: LinearMPCProblem, x_start: np.ndarray, time_index: int, u_prev: np.ndarray, warm_start: np.ndarray | None = None) -> dict[str, Any]:
    """Solve one finite-horizon MPC optimization problem."""

    if warm_start is None:
        u0 = np.repeat(problem.u_ref[time_index].reshape(1, -1), problem.horizon, axis=0)
    else:
        u0 = warm_start.reshape(problem.horizon, problem.nu).copy()

    bounds = []
    for _ in range(problem.horizon):
        for j in range(problem.nu):
            lo = None if problem.u_min is None else float(problem.u_min[j])
            hi = None if problem.u_max is None else float(problem.u_max[j])
            bounds.append((lo, hi))

    constraints = []
    if problem.x_min is not None or problem.x_max is not None:
        constraints.extend(_state_constraints(problem, x_start, time_index))
    if problem.du_min is not None or problem.du_max is not None:
        constraints.extend(_delta_u_constraints(problem, u_prev))

    result = minimize(
        fun=lambda z: horizon_cost(problem, x_start, z, time_index, u_prev),
        x0=u0.reshape(-1),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 250, "ftol": 1e-8, "disp": False},
    )

    U = result.x.reshape(problem.horizon, problem.nu)
    X = rollout(problem, x_start, U, time_index)
    return {
        "success": bool(result.success),
        "status": int(result.status),
        "message": str(result.message),
        "cost": float(result.fun) if np.isfinite(result.fun) else float("nan"),
        "U": U,
        "X": X,
        "nit": int(getattr(result, "nit", -1)),
    }


def _state_constraints(problem: LinearMPCProblem, x_start: np.ndarray, time_index: int) -> list[dict[str, Any]]:
    constraints: list[dict[str, Any]] = []

    if problem.x_min is not None:
        for k in range(1, problem.horizon + 1):
            for i in range(problem.nx):
                lo = float(problem.x_min[i])
                constraints.append({
                    "type": "ineq",
                    "fun": lambda z, kk=k, ii=i, low=lo: rollout(problem, x_start, z.reshape(problem.horizon, problem.nu), time_index)[kk, ii] - low,
                })

    if problem.x_max is not None:
        for k in range(1, problem.horizon + 1):
            for i in range(problem.nx):
                hi = float(problem.x_max[i])
                constraints.append({
                    "type": "ineq",
                    "fun": lambda z, kk=k, ii=i, high=hi: high - rollout(problem, x_start, z.reshape(problem.horizon, problem.nu), time_index)[kk, ii],
                })

    return constraints


def _delta_u_constraints(problem: LinearMPCProblem, u_prev: np.ndarray) -> list[dict[str, Any]]:
    constraints: list[dict[str, Any]] = []

    def delta_at(z: np.ndarray, k: int, j: int) -> float:
        U = z.reshape(problem.horizon, problem.nu)
        prev = u_prev[j] if k == 0 else U[k - 1, j]
        return float(U[k, j] - prev)

    if problem.du_min is not None:
        for k in range(problem.horizon):
            for j in range(problem.nu):
                lo = float(problem.du_min[j])
                constraints.append({"type": "ineq", "fun": lambda z, kk=k, jj=j, low=lo: delta_at(z, kk, jj) - low})

    if problem.du_max is not None:
        for k in range(problem.horizon):
            for j in range(problem.nu):
                hi = float(problem.du_max[j])
                constraints.append({"type": "ineq", "fun": lambda z, kk=k, jj=j, high=hi: high - delta_at(z, kk, jj)})

    return constraints


def simulate_mpc(problem: LinearMPCProblem) -> dict[str, Any]:
    """Run receding-horizon closed-loop MPC simulation."""

    X = np.zeros((problem.steps + 1, problem.nx))
    U = np.zeros((problem.steps, problem.nu))
    costs = np.zeros(problem.steps)
    success = np.zeros(problem.steps, dtype=bool)
    messages: list[str] = []
    X[0] = problem.x0

    u_prev = np.zeros(problem.nu)
    warm: np.ndarray | None = None

    for t in range(problem.steps):
        sol = solve_open_loop(problem, X[t], t, u_prev, warm_start=warm)
        success[t] = bool(sol["success"])
        messages.append(sol["message"])
        costs[t] = float(sol["cost"])

        planned_U = sol["U"]
        if not sol["success"]:
            planned_U = _fallback_input(problem, t, u_prev)

        U[t] = planned_U[0]
        A, B = get_AB(problem, t)
        X[t + 1] = A @ X[t] + B @ U[t] + problem.d[t]
        u_prev = U[t]

        if planned_U.shape[0] > 1:
            warm = np.vstack([planned_U[1:], planned_U[-1:]])
        else:
            warm = planned_U.copy()

    return {
        "analysis_type": "lti_ltv_mpc_simulation",
        "dt": problem.dt,
        "steps": problem.steps,
        "horizon": problem.horizon,
        "state_names": problem.state_names,
        "input_names": problem.input_names,
        "time": np.arange(problem.steps + 1) * problem.dt,
        "time_u": np.arange(problem.steps) * problem.dt,
        "X": X,
        "U": U,
        "x_ref": problem.x_ref[: problem.steps + 1],
        "u_ref": problem.u_ref[: problem.steps],
        "costs": costs,
        "success": success,
        "messages": messages,
        "final_state": X[-1],
        "all_optimizations_successful": bool(np.all(success)),
    }


def _fallback_input(problem: LinearMPCProblem, time_index: int, u_prev: np.ndarray) -> np.ndarray:
    """Return a safe fallback input sequence if SLSQP fails."""

    U = np.repeat(u_prev.reshape(1, -1), problem.horizon, axis=0)
    if problem.u_min is not None:
        U = np.maximum(U, problem.u_min.reshape(1, -1))
    if problem.u_max is not None:
        U = np.minimum(U, problem.u_max.reshape(1, -1))
    return U


def run_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Parse and execute one MPC input specification."""

    problem = parse_problem(spec)
    result = simulate_mpc(problem)
    result["title"] = spec.get("title", "Model Predictive Control run")
    result["plant"] = spec.get("plant", "linear_state_space")
    return result


def build_thermal_cooling_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Build a small four-state automotive thermal-control demo.

    The model is intentionally simple and educational. The states are combustion
    wall, coolant-out, block-metal, and radiator outlet temperatures. The inputs
    are normalized pump command and fan command. The generated matrices vary with
    a load profile, producing an LTV-like plant that can be used before replacing
    the demo with calibrated engine-cooling data.
    """

    steps = int(spec.get("steps", 80))
    horizon = int(spec.get("horizon", 12))
    dt = float(spec.get("dt", 1.0))
    total = steps + horizon + 1

    load = np.asarray(spec.get("engine_load_profile", []), dtype=float)
    if load.size == 0:
        idx = np.arange(total)
        load = 0.45 + 0.35 * (idx > total * 0.25) + 0.20 * (idx > total * 0.55)
    if load.size < total:
        load = np.concatenate([load, np.repeat(load[-1], total - load.size)])
    load = load[:total]

    ambient = float(spec.get("ambient_temp_c", 35.0))
    A_seq = []
    B_seq = []
    d_seq = []
    for ell in load:
        thermal_gain = 0.025 + 0.035 * ell
        A = np.array([
            [0.965 - 0.015 * ell, 0.020, 0.010, 0.000],
            [0.030, 0.925, 0.020, 0.015],
            [0.015, 0.020, 0.950, 0.000],
            [0.000, 0.060, 0.000, 0.900],
        ])
        B = np.array([
            [-0.25, -0.02],
            [-0.40, -0.08],
            [-0.10, -0.02],
            [-0.12, -0.55],
        ]) * dt
        d = np.array([
            thermal_gain * 42.0 + 0.002 * ambient,
            thermal_gain * 25.0 + 0.003 * ambient,
            thermal_gain * 18.0 + 0.001 * ambient,
            0.015 * ambient,
        ]) * dt
        A_seq.append(A)
        B_seq.append(B)
        d_seq.append(d)

    generated = dict(spec)
    generated["model"] = {
        "A": A_seq[0].tolist(),
        "B": B_seq[0].tolist(),
        "A_sequence": np.asarray(A_seq).tolist(),
        "B_sequence": np.asarray(B_seq).tolist(),
        "d": np.asarray(d_seq).tolist(),
        "dt": dt,
    }
    generated.setdefault("x0", [115.0, 98.0, 108.0, 88.0])
    generated.setdefault("x_ref", [105.0, 92.0, 100.0, 82.0])
    generated.setdefault("state_names", ["wall_temp_c", "coolant_out_c", "block_temp_c", "radiator_out_c"])
    generated.setdefault("input_names", ["pump_command", "fan_command"])
    generated.setdefault("weights", {
        "Q": [4.0, 5.0, 2.0, 1.0],
        "R": [0.05, 0.08],
        "P": [8.0, 10.0, 4.0, 2.0],
        "Rd": [0.25, 0.35],
    })
    generated.setdefault("constraints", {
        "u_min": [0.0, 0.0],
        "u_max": [1.0, 1.0],
        "du_min": [-0.15, -0.15],
        "du_max": [0.15, 0.15],
        "x_min": [70.0, 60.0, 70.0, 50.0],
        "x_max": [125.0, 110.0, 120.0, 105.0],
    })
    generated["steps"] = steps
    generated["horizon"] = horizon
    generated["dt"] = dt
    return generated
