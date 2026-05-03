#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Core numerical routines for discrete-time model predictive control.

The module intentionally keeps the original transparent SciPy/SLSQP route as
its default native solver. A separate optional CasADi/Opti route is available
when an input specification sets ``solver.backend`` to ``"casadi_opti"``.

The native route is useful for learning and debugging the MPC mechanics. The
CasADi route is useful for experimenting with a Rawlings-style optimization
formulation without replacing the package architecture.
"""

from dataclasses import dataclass, field
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


NATIVE_BACKENDS = {"native", "native_slsqp", "scipy", "scipy_slsqp", "slsqp"}
CASADI_BACKENDS = {"casadi", "casadi_opti", "opti", "ipopt", "casadi_ipopt"}


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
    solver_backend: str = "native_slsqp"
    solver_options: dict[str, Any] = field(default_factory=dict)

    @property
    def nx(self) -> int:
        return int(self.A.shape[0])

    @property
    def nu(self) -> int:
        return int(self.B.shape[1])


@dataclass(frozen=True)
class SolverConfig:
    """Parsed solver configuration from the input specification."""

    backend: str
    options: dict[str, Any]


def parse_solver_config(spec: dict[str, Any]) -> SolverConfig:
    """Parse and normalize the solver configuration.

    Supported backends are:

    - ``native_slsqp``: the original NumPy/SciPy implementation.
    - ``casadi_opti``: an optional CasADi Opti/IPOPT implementation.
    """

    raw = spec.get("solver", {})
    if isinstance(raw, str):
        backend = raw
        options: dict[str, Any] = {}
    elif isinstance(raw, dict):
        backend = str(raw.get("backend", raw.get("name", spec.get("backend", "native_slsqp"))))
        options = {k: v for k, v in raw.items() if k not in {"backend", "name"}}
    else:
        raise InputError("solver must be a string or object when provided")

    backend_key = backend.strip().lower().replace("-", "_")
    if backend_key in NATIVE_BACKENDS:
        return SolverConfig(backend="native_slsqp", options=options)
    if backend_key in CASADI_BACKENDS:
        return SolverConfig(backend="casadi_opti", options=options)
    raise InputError(
        f"Unsupported solver backend {backend!r}. Use 'native_slsqp' or 'casadi_opti'."
    )


def parse_problem(spec: dict[str, Any]) -> LinearMPCProblem:
    """Parse a dictionary into a normalized linear MPC problem."""

    plant = str(spec.get("plant", "linear_state_space")).lower()
    if plant in {"thermal_cooling_4state_demo", "automotive_thermal_cooling_demo"}:
        spec = build_thermal_cooling_spec(spec)

    solver = parse_solver_config(spec)
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
        solver_backend=solver.backend,
        solver_options=solver.options,
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




def _coerce_trajectory(value: Any, rows: int, cols: int, name: str) -> np.ndarray:
    """Coerce solver output into a strict 2-D trajectory array.

    CasADi may return a one-dimensional NumPy array when one dimension is one,
    for example an input trajectory with one actuator. The rest of the package
    expects trajectories with shape ``(rows, cols)``. This helper keeps the
    native and CasADi routes compatible for both SISO and MIMO problems.
    """

    arr = np.asarray(value, dtype=float)

    if arr.shape == (rows, cols):
        out = arr.copy()
    elif arr.shape == (cols, rows):
        out = arr.T.copy()
    elif arr.ndim == 1 and cols == 1 and arr.size == rows:
        out = arr.reshape(rows, 1).copy()
    elif arr.ndim == 1 and rows == 1 and arr.size == cols:
        out = arr.reshape(1, cols).copy()
    elif arr.size == rows * cols:
        out = arr.reshape(rows, cols).copy()
    else:
        raise InputError(f"{name} must have shape {(rows, cols)}; got {arr.shape}")

    if not np.all(np.isfinite(out)):
        raise InputError(f"{name} contains non-finite values")
    return out


def _coerce_input_plan(problem: LinearMPCProblem, value: Any, name: str = "planned_U") -> np.ndarray:
    """Return an input plan with shape ``(horizon, nu)``."""

    return _coerce_trajectory(value, problem.horizon, problem.nu, name)


def _coerce_state_plan(problem: LinearMPCProblem, value: Any, name: str = "planned_X") -> np.ndarray:
    """Return a state plan with shape ``(horizon + 1, nx)``."""

    return _coerce_trajectory(value, problem.horizon + 1, problem.nx, name)

def solve_open_loop(problem: LinearMPCProblem, x_start: np.ndarray, time_index: int, u_prev: np.ndarray, warm_start: np.ndarray | None = None) -> dict[str, Any]:
    """Solve one finite-horizon MPC optimization problem with SciPy SLSQP."""

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

    maxiter = int(problem.solver_options.get("maxiter", problem.solver_options.get("max_iter", 250)))
    ftol = float(problem.solver_options.get("ftol", 1e-8))
    disp = bool(problem.solver_options.get("disp", False))

    result = minimize(
        fun=lambda z: horizon_cost(problem, x_start, z, time_index, u_prev),
        x0=u0.reshape(-1),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": maxiter, "ftol": ftol, "disp": disp},
    )

    U = result.x.reshape(problem.horizon, problem.nu)
    X = rollout(problem, x_start, U, time_index)
    return {
        "solver": "native_slsqp",
        "success": bool(result.success),
        "status": int(result.status),
        "message": str(result.message),
        "cost": float(result.fun) if np.isfinite(result.fun) else float("nan"),
        "U": U,
        "X": X,
        "nit": int(getattr(result, "nit", -1)),
    }


def solve_open_loop_casadi(problem: LinearMPCProblem, x_start: np.ndarray, time_index: int, u_prev: np.ndarray, warm_start: np.ndarray | None = None) -> dict[str, Any]:
    """Solve one finite-horizon MPC optimization problem with CasADi Opti.

    The formulation mirrors the native solver: same linear/LTV model, same
    quadratic objective, same input/state/rate constraints. CasADi is imported
    lazily so the native solver still works on machines without CasADi.
    """

    try:
        import casadi as ca  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on local environment
        raise InputError(
            "CasADi backend requested, but the 'casadi' package is not importable. "
            "Install casadi or switch solver.backend to 'native_slsqp'."
        ) from exc

    if warm_start is None:
        u0 = np.repeat(problem.u_ref[time_index].reshape(1, -1), problem.horizon, axis=0)
    else:
        u0 = warm_start.reshape(problem.horizon, problem.nu).copy()
    if problem.u_min is not None:
        u0 = np.maximum(u0, problem.u_min.reshape(1, -1))
    if problem.u_max is not None:
        u0 = np.minimum(u0, problem.u_max.reshape(1, -1))

    x0_pred = rollout(problem, x_start, u0, time_index)

    opti = ca.Opti()
    X = opti.variable(problem.nx, problem.horizon + 1)
    U = opti.variable(problem.nu, problem.horizon)

    def dm_vec(value: np.ndarray) -> Any:
        return ca.DM(np.asarray(value, dtype=float).reshape(-1, 1))

    def quad(expr: Any, weight: np.ndarray) -> Any:
        W = ca.DM(weight)
        return ca.mtimes([expr.T, W, expr])

    opti.subject_to(X[:, 0] == dm_vec(x_start))
    cost = 0
    prev = dm_vec(u_prev)

    for k in range(problem.horizon):
        A, B = get_AB(problem, time_index + k)
        d_k = dm_vec(problem.d[time_index + k])
        opti.subject_to(X[:, k + 1] == ca.mtimes(ca.DM(A), X[:, k]) + ca.mtimes(ca.DM(B), U[:, k]) + d_k)

        x_err = X[:, k] - dm_vec(problem.x_ref[time_index + k])
        u_err = U[:, k] - dm_vec(problem.u_ref[time_index + k])
        du = U[:, k] - prev
        cost = cost + quad(x_err, problem.Q) + quad(u_err, problem.R) + quad(du, problem.Rd)
        prev = U[:, k]

        for j in range(problem.nu):
            if problem.u_min is not None:
                opti.subject_to(U[j, k] >= float(problem.u_min[j]))
            if problem.u_max is not None:
                opti.subject_to(U[j, k] <= float(problem.u_max[j]))
            if problem.du_min is not None:
                opti.subject_to(du[j] >= float(problem.du_min[j]))
            if problem.du_max is not None:
                opti.subject_to(du[j] <= float(problem.du_max[j]))

        for i in range(problem.nx):
            if problem.x_min is not None:
                opti.subject_to(X[i, k + 1] >= float(problem.x_min[i]))
            if problem.x_max is not None:
                opti.subject_to(X[i, k + 1] <= float(problem.x_max[i]))

    x_terminal = X[:, problem.horizon] - dm_vec(problem.x_ref[time_index + problem.horizon])
    cost = cost + quad(x_terminal, problem.P)
    opti.minimize(cost)

    opti.set_initial(U, u0.T)
    opti.set_initial(X, x0_pred.T)

    print_level = int(problem.solver_options.get("print_level", problem.solver_options.get("ipopt_print_level", 0)))
    max_iter = int(problem.solver_options.get("max_iter", problem.solver_options.get("maxiter", 200)))
    tol = float(problem.solver_options.get("tol", 1e-8))
    acceptable_tol = float(problem.solver_options.get("acceptable_tol", 1e-6))
    expand = bool(problem.solver_options.get("expand", False))

    p_opts = {"expand": expand, "print_time": bool(problem.solver_options.get("print_time", False))}
    s_opts = {
        "print_level": print_level,
        "max_iter": max_iter,
        "tol": tol,
        "acceptable_tol": acceptable_tol,
    }
    opti.solver("ipopt", p_opts, s_opts)

    try:
        sol = opti.solve()
        U_opt = _coerce_input_plan(problem, sol.value(U), name="casadi_U")
        X_opt = _coerce_state_plan(problem, sol.value(X), name="casadi_X")
        cost_value = float(sol.value(cost))
        stats = sol.stats()
        return {
            "solver": "casadi_opti",
            "success": bool(stats.get("success", True)),
            "status": 0,
            "message": str(stats.get("return_status", "Solve_Succeeded")),
            "cost": cost_value,
            "U": U_opt,
            "X": X_opt,
            "nit": int(stats.get("iter_count", -1)),
        }
    except Exception as exc:  # pragma: no cover - depends on local solver behavior
        # Keep the closed-loop simulation alive. simulate_mpc will switch to the
        # package fallback command because success is False.
        return {
            "solver": "casadi_opti",
            "success": False,
            "status": 1,
            "message": f"CasADi solve failed: {exc.__class__.__name__}: {exc}",
            "cost": float(horizon_cost(problem, x_start, u0.reshape(-1), time_index, u_prev)),
            "U": u0,
            "X": x0_pred,
            "nit": -1,
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


def _select_open_loop_solver(problem: LinearMPCProblem):
    if problem.solver_backend == "native_slsqp":
        return solve_open_loop
    if problem.solver_backend == "casadi_opti":
        return solve_open_loop_casadi
    raise InputError(f"Unsupported solver backend: {problem.solver_backend}")


def simulate_mpc(problem: LinearMPCProblem) -> dict[str, Any]:
    """Run receding-horizon closed-loop MPC simulation."""

    X = np.zeros((problem.steps + 1, problem.nx))
    U = np.zeros((problem.steps, problem.nu))
    costs = np.zeros(problem.steps)
    success = np.zeros(problem.steps, dtype=bool)
    nit = np.zeros(problem.steps, dtype=int)
    messages: list[str] = []
    X[0] = problem.x0

    u_prev = np.zeros(problem.nu)
    warm: np.ndarray | None = None
    open_loop_solver = _select_open_loop_solver(problem)

    for t in range(problem.steps):
        sol = open_loop_solver(problem, X[t], t, u_prev, warm_start=warm)
        success[t] = bool(sol["success"])
        messages.append(sol["message"])
        costs[t] = float(sol["cost"])
        nit[t] = int(sol.get("nit", -1))

        planned_U = _coerce_input_plan(problem, sol["U"])
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
        "solver_backend": problem.solver_backend,
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
        "solver_iterations": nit,
        "final_state": X[-1],
        "all_optimizations_successful": bool(np.all(success)),
    }


def _fallback_input(problem: LinearMPCProblem, time_index: int, u_prev: np.ndarray) -> np.ndarray:
    """Return a safe fallback input sequence if an optimizer fails."""

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
