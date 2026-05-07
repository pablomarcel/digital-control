#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
tracking.py

Rawlings, Mayne, and Diehl Section 1.5.1 sandbox:
Tracking nonzero setpoints with steady-state targets and deviation variables.

This script is intentionally standalone. It demonstrates the mechanics in
Section 1.5.1:

1. Solve a steady-state target problem for (xs, us).
2. Shift coordinates to deviation variables:
       x_e(k) = x(k) - xs
       u_e(k) = u(k) - us
3. Apply an ordinary zero-regulation LQR controller to the deviation system:
       x_e(k+1) = A x_e(k) + B u_e(k)
4. Apply the real plant input:
       u(k) = us + u_e(k)
5. Show why H is introduced when there are more measured outputs than inputs.
6. Show why input preferences usp are useful when there are more inputs than outputs.

Outputs are written to:
    out/tracking

Run:
    python tracking.py
"""

from dataclasses import dataclass
from pathlib import Path
import csv
import json
import math
import zipfile
from typing import Any

import numpy as np
import matplotlib.pyplot as plt

try:
    from scipy.linalg import solve_discrete_are
except Exception as exc:  # pragma: no cover
    solve_discrete_are = None
    _SCIPY_IMPORT_ERROR = exc


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def mat_str(a: np.ndarray, precision: int = 8) -> str:
    return np.array2string(np.asarray(a), precision=precision, suppress_small=False)


def jsonable(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        if np.iscomplexobj(value):
            return jsonable(value.tolist())
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, (complex, np.complexfloating)):
        return {"real": float(np.real(value)), "imag": float(np.imag(value))}
    if isinstance(value, list):
        return [jsonable(v) for v in value]
    if isinstance(value, tuple):
        return [jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    return value


def spectral_radius(a: np.ndarray) -> float:
    vals = np.linalg.eigvals(a)
    return float(np.max(np.abs(vals)))


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    headers = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in headers})


# ---------------------------------------------------------------------------
# Target selector and deviation regulator
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TrackingCase:
    name: str
    description: str
    A: np.ndarray
    B: np.ndarray
    C: np.ndarray
    H: np.ndarray
    ysp: np.ndarray
    rsp: np.ndarray
    usp: np.ndarray
    Qs: np.ndarray
    Rs: np.ndarray
    Qreg: np.ndarray
    Rreg: np.ndarray
    x0: np.ndarray
    steps: int = 40


@dataclass(frozen=True)
class TargetSolution:
    z: np.ndarray
    xs: np.ndarray
    us: np.ndarray
    ys: np.ndarray
    rs: np.ndarray
    objective: float
    equality_residual: np.ndarray
    rank_M: int
    rank_augmented: int
    feasible_equalities: bool
    kkt_residual_norm: float
    condition_KKT: float


def solve_steady_state_target(case: TrackingCase) -> TargetSolution:
    """Solve the equality-only form of Rawlings equation (1.41).

    Objective:
        1/2 |us - usp|^2_Rs + 1/2 |C xs - ysp|^2_Qs

    Equalities:
        (I - A) xs - B us = 0
        H C xs = rsp
    """
    A, B, C, H = case.A, case.B, case.C, case.H
    n = A.shape[0]
    m = B.shape[1]

    M_dyn = np.hstack([np.eye(n) - A, -B])
    M_ctl = np.hstack([H @ C, np.zeros((H.shape[0], m))])
    M = np.vstack([M_dyn, M_ctl])
    b = np.concatenate([np.zeros(n), case.rsp])

    # Feasibility check for the equality constraints.
    rank_M = int(np.linalg.matrix_rank(M, tol=1e-10))
    rank_aug = int(np.linalg.matrix_rank(np.column_stack([M, b]), tol=1e-10))
    feasible = rank_M == rank_aug
    if not feasible:
        # Return least-squares target for diagnostics. The log will call this out.
        z_ls = np.linalg.lstsq(M, b, rcond=None)[0]
        xs = z_ls[:n]
        us = z_ls[n:]
        ys = C @ xs
        rs = H @ ys
        err_y = ys - case.ysp
        err_u = us - case.usp
        obj = 0.5 * float(err_u.T @ case.Rs @ err_u + err_y.T @ case.Qs @ err_y)
        return TargetSolution(
            z=z_ls,
            xs=xs,
            us=us,
            ys=ys,
            rs=rs,
            objective=obj,
            equality_residual=M @ z_ls - b,
            rank_M=rank_M,
            rank_augmented=rank_aug,
            feasible_equalities=False,
            kkt_residual_norm=float("nan"),
            condition_KKT=float("nan"),
        )

    # Quadratic objective in z = [xs; us].
    G = np.zeros((n + m, n + m))
    G[:n, :n] = C.T @ case.Qs @ C
    G[n:, n:] = case.Rs
    g = np.concatenate([-C.T @ case.Qs @ case.ysp, -case.Rs @ case.usp])

    KKT = np.block([
        [G, M.T],
        [M, np.zeros((M.shape[0], M.shape[0]))],
    ])
    rhs = np.concatenate([-g, b])

    # KKT may be singular in semidefinite cases, so use least squares robustly.
    sol, *_ = np.linalg.lstsq(KKT, rhs, rcond=None)
    z = sol[:n + m]
    kkt_resid = KKT @ sol - rhs

    xs = z[:n]
    us = z[n:]
    ys = C @ xs
    rs = H @ ys
    err_y = ys - case.ysp
    err_u = us - case.usp
    obj = 0.5 * float(err_u.T @ case.Rs @ err_u + err_y.T @ case.Qs @ err_y)

    return TargetSolution(
        z=z,
        xs=xs,
        us=us,
        ys=ys,
        rs=rs,
        objective=obj,
        equality_residual=M @ z - b,
        rank_M=rank_M,
        rank_augmented=rank_aug,
        feasible_equalities=True,
        kkt_residual_norm=float(np.linalg.norm(kkt_resid)),
        condition_KKT=float(np.linalg.cond(KKT)),
    )


def lqr_gain(A: np.ndarray, B: np.ndarray, Q: np.ndarray, R: np.ndarray) -> dict[str, Any]:
    """Return stabilizing discrete-time LQR gain for u = K x."""
    if solve_discrete_are is None:  # pragma: no cover
        raise RuntimeError(f"scipy.linalg.solve_discrete_are is required: {_SCIPY_IMPORT_ERROR}")
    P = solve_discrete_are(A, B, Q, R)
    # Standard minimizer is u = - (R + B'PB)^-1 B'PA x.
    K = -np.linalg.solve(R + B.T @ P @ B, B.T @ P @ A)
    Acl = A + B @ K
    return {
        "P": P,
        "K": K,
        "Acl": Acl,
        "eig_Acl": np.linalg.eigvals(Acl),
        "rho_Acl": spectral_radius(Acl),
    }


def simulate_tracking(case: TrackingCase, target: TargetSolution) -> dict[str, Any]:
    A, B, C, H = case.A, case.B, case.C, case.H
    n = A.shape[0]
    m = B.shape[1]
    p = C.shape[0]
    nc = H.shape[0]

    lqr = lqr_gain(A, B, case.Qreg, case.Rreg)
    K = lqr["K"]

    X = np.zeros((case.steps + 1, n))
    U = np.zeros((case.steps, m))
    Y = np.zeros((case.steps + 1, p))
    Rvar = np.zeros((case.steps + 1, nc))
    Xdev = np.zeros_like(X)
    Udev = np.zeros_like(U)
    stage_cost = np.zeros(case.steps)

    X[0] = case.x0
    Y[0] = C @ X[0]
    Rvar[0] = H @ Y[0]
    Xdev[0] = X[0] - target.xs

    for k in range(case.steps):
        xe = X[k] - target.xs
        ue = K @ xe
        u = target.us + ue
        Udev[k] = ue
        U[k] = u
        stage_cost[k] = 0.5 * float(xe.T @ case.Qreg @ xe + ue.T @ case.Rreg @ ue)
        X[k + 1] = A @ X[k] + B @ u
        Y[k + 1] = C @ X[k + 1]
        Rvar[k + 1] = H @ Y[k + 1]
        Xdev[k + 1] = X[k + 1] - target.xs

    rows = []
    for k in range(case.steps + 1):
        row: dict[str, Any] = {"k": k}
        for i in range(n):
            row[f"x{i + 1}"] = float(X[k, i])
            row[f"x{i + 1}_target"] = float(target.xs[i])
            row[f"x{i + 1}_dev"] = float(Xdev[k, i])
        for i in range(p):
            row[f"y{i + 1}"] = float(Y[k, i])
            row[f"y{i + 1}_setpoint"] = float(case.ysp[i])
            row[f"y{i + 1}_target"] = float(target.ys[i])
        for i in range(nc):
            row[f"r{i + 1}"] = float(Rvar[k, i])
            row[f"r{i + 1}_setpoint"] = float(case.rsp[i])
        row["x_deviation_norm"] = float(np.linalg.norm(Xdev[k]))
        row["y_setpoint_error_norm"] = float(np.linalg.norm(Y[k] - case.ysp))
        row["r_setpoint_error_norm"] = float(np.linalg.norm(Rvar[k] - case.rsp))
        if k < case.steps:
            for j in range(m):
                row[f"u{j + 1}"] = float(U[k, j])
                row[f"u{j + 1}_target"] = float(target.us[j])
                row[f"u{j + 1}_dev"] = float(Udev[k, j])
            row["stage_cost"] = float(stage_cost[k])
        else:
            for j in range(m):
                row[f"u{j + 1}"] = ""
                row[f"u{j + 1}_target"] = float(target.us[j])
                row[f"u{j + 1}_dev"] = ""
            row["stage_cost"] = ""
        rows.append(row)

    return {
        "lqr": lqr,
        "X": X,
        "U": U,
        "Y": Y,
        "Rvar": Rvar,
        "Xdev": Xdev,
        "Udev": Udev,
        "stage_cost": stage_cost,
        "rows": rows,
        "final_output_error_norm": float(np.linalg.norm(Y[-1] - case.ysp)),
        "final_controlled_error_norm": float(np.linalg.norm(Rvar[-1] - case.rsp)),
        "final_deviation_norm": float(np.linalg.norm(Xdev[-1])),
    }


def simulate_wrong_zero_regulator(case: TrackingCase) -> dict[str, Any]:
    """Regulate original x to zero, intentionally ignoring tracking target."""
    lqr = lqr_gain(case.A, case.B, case.Qreg, case.Rreg)
    K = lqr["K"]
    X = np.zeros((case.steps + 1, case.A.shape[0]))
    U = np.zeros((case.steps, case.B.shape[1]))
    Y = np.zeros((case.steps + 1, case.C.shape[0]))
    Rvar = np.zeros((case.steps + 1, case.H.shape[0]))
    X[0] = case.x0
    Y[0] = case.C @ X[0]
    Rvar[0] = case.H @ Y[0]
    for k in range(case.steps):
        u = K @ X[k]
        U[k] = u
        X[k + 1] = case.A @ X[k] + case.B @ u
        Y[k + 1] = case.C @ X[k + 1]
        Rvar[k + 1] = case.H @ Y[k + 1]
    return {"X": X, "U": U, "Y": Y, "Rvar": Rvar, "lqr": lqr}


# ---------------------------------------------------------------------------
# Plotting and logging
# ---------------------------------------------------------------------------


def plot_case(case: TrackingCase, target: TargetSolution, sim: dict[str, Any], out_dir: Path) -> list[Path]:
    paths: list[Path] = []
    kx = np.arange(case.steps + 1)
    ku = np.arange(case.steps)
    X = sim["X"]
    U = sim["U"]
    Y = sim["Y"]
    Rvar = sim["Rvar"]
    Xdev = sim["Xdev"]

    # Output plot.
    fig, ax = plt.subplots(figsize=(10, 5.8))
    for i in range(case.C.shape[0]):
        ax.plot(kx, Y[:, i], label=f"y{i + 1}")
        ax.axhline(case.ysp[i], linestyle="--", linewidth=1.0, label=f"y{i + 1} setpoint")
        ax.axhline(target.ys[i], linestyle=":", linewidth=1.0, label=f"y{i + 1} target")
    for j in range(case.H.shape[0]):
        ax.plot(kx, Rvar[:, j], linewidth=2.3, label=f"controlled r{j + 1}=H y")
        ax.axhline(case.rsp[j], linestyle="-.", linewidth=1.0, label=f"r{j + 1} setpoint")
    ax.set_title(f"{case.name}: outputs and controlled variables")
    ax.set_xlabel("k")
    ax.set_ylabel("output / controlled-variable value")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path = out_dir / f"{case.name}_outputs.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    paths.append(path)

    # Inputs plot.
    fig, ax = plt.subplots(figsize=(10, 4.8))
    for j in range(case.B.shape[1]):
        ax.step(ku, U[:, j], where="post", label=f"u{j + 1}")
        ax.axhline(target.us[j], linestyle="--", linewidth=1.0, label=f"u{j + 1} target")
        ax.axhline(case.usp[j], linestyle=":", linewidth=1.0, label=f"u{j + 1} preferred")
    ax.set_title(f"{case.name}: actual input u = us + ue")
    ax.set_xlabel("k")
    ax.set_ylabel("input value")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path = out_dir / f"{case.name}_inputs.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    paths.append(path)

    # Deviation convergence plot.
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.semilogy(kx, np.linalg.norm(Xdev, axis=1), marker="o", markersize=3, label="||x - xs||")
    ax.semilogy(ku, sim["stage_cost"], marker="s", markersize=3, label="stage cost in deviation variables")
    ax.set_title(f"{case.name}: zero-regulation problem after coordinate shift")
    ax.set_xlabel("k")
    ax.set_ylabel("log scale")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path = out_dir / f"{case.name}_deviation_convergence.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    paths.append(path)

    # State plot.
    fig, ax = plt.subplots(figsize=(10, 5.2))
    for i in range(case.A.shape[0]):
        ax.plot(kx, X[:, i], label=f"x{i + 1}")
        ax.axhline(target.xs[i], linestyle="--", linewidth=1.0, label=f"x{i + 1} target")
    ax.set_title(f"{case.name}: states move to steady-state target xs")
    ax.set_xlabel("k")
    ax.set_ylabel("state value")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path = out_dir / f"{case.name}_states.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    paths.append(path)

    return paths


def plot_wrong_vs_shifted(case: TrackingCase, target: TargetSolution, sim: dict[str, Any], wrong: dict[str, Any], out_dir: Path) -> Path:
    kx = np.arange(case.steps + 1)
    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.plot(kx, sim["Y"][:, 0], label="correct shifted regulator output y")
    ax.plot(kx, wrong["Y"][:, 0], linestyle="--", label="wrong zero-regulator output y")
    ax.axhline(case.ysp[0], linestyle=":", linewidth=1.2, label="desired setpoint ysp")
    ax.axhline(target.ys[0], linestyle="-.", linewidth=1.0, label="target output C xs")
    ax.set_title("Why Section 1.5.1 shifts coordinates before regulating")
    ax.set_xlabel("k")
    ax.set_ylabel("output y")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path = out_dir / "exact_siso_shifted_vs_wrong_zero_regulation.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def log_case(case: TrackingCase, target: TargetSolution, sim: dict[str, Any], wrong: dict[str, Any] | None = None) -> str:
    A, B, C, H = case.A, case.B, case.C, case.H
    n, m, p, nc = A.shape[0], B.shape[1], C.shape[0], H.shape[0]
    lqr = sim["lqr"]

    M_dyn = np.hstack([np.eye(n) - A, -B])
    M_ctl = np.hstack([H @ C, np.zeros((nc, m))])
    M = np.vstack([M_dyn, M_ctl])
    b = np.concatenate([np.zeros(n), case.rsp])

    lines: list[str] = []
    lines.append("=" * 88)
    lines.append(f"Case: {case.name}")
    lines.append(case.description)
    lines.append("")
    lines.append("Model")
    lines.append("  x(k+1) = A x(k) + B u(k)")
    lines.append("  y(k)   = C x(k)")
    lines.append(f"  n={n}, m={m}, p={p}, controlled-variable dimension nc={nc}")
    lines.append("  A =")
    lines.append(mat_str(A))
    lines.append("  B =")
    lines.append(mat_str(B))
    lines.append("  C =")
    lines.append(mat_str(C))
    lines.append("  H =")
    lines.append(mat_str(H))
    lines.append(f"  ysp = {case.ysp}")
    lines.append(f"  rsp = {case.rsp}")
    lines.append(f"  usp = {case.usp}")
    lines.append("")
    lines.append("Rawlings Section 1.5.1 target equations")
    lines.append("  Steady state requires: (I - A) xs - B us = 0")
    lines.append("  Controlled-variable target requires: H C xs = rsp")
    lines.append("  Target optimizer uses:")
    lines.append("    min 1/2 |us-usp|^2_Rs + 1/2 |Cxs-ysp|^2_Qs")
    lines.append("    s.t. [(I-A)  -B;  H C  0] [xs; us] = [0; rsp]")
    lines.append("  Equality matrix M =")
    lines.append(mat_str(M))
    lines.append(f"  RHS b = {b}")
    lines.append(f"  rank(M) = {target.rank_M}")
    lines.append(f"  rank([M b]) = {target.rank_augmented}")
    lines.append(f"  feasible equalities? {target.feasible_equalities}")
    lines.append("")
    lines.append("Target solution")
    lines.append(f"  xs = {target.xs}")
    lines.append(f"  us = {target.us}")
    lines.append(f"  ys = C xs = {target.ys}")
    lines.append(f"  rs = H ys = {target.rs}")
    lines.append(f"  target objective = {target.objective:.12g}")
    lines.append(f"  equality residual = {target.equality_residual}")
    lines.append(f"  ||equality residual|| = {np.linalg.norm(target.equality_residual):.12e}")
    lines.append(f"  KKT residual norm = {target.kkt_residual_norm:.12e}")
    lines.append(f"  KKT condition number = {target.condition_KKT:.12e}")
    lines.append("")
    lines.append("Deviation-variable regulator")
    lines.append("  Define xe(k) = x(k) - xs and ue(k) = u(k) - us.")
    lines.append("  Then xe(k+1) = A xe(k) + B ue(k).")
    lines.append("  LQR solves zero regulation in these deviation variables.")
    lines.append("  Riccati P =")
    lines.append(mat_str(lqr["P"]))
    lines.append("  Feedback gain K for ue = K xe =")
    lines.append(mat_str(lqr["K"]))
    lines.append("  Closed-loop A + B K =")
    lines.append(mat_str(lqr["Acl"]))
    eig = lqr["eig_Acl"]
    lines.append(f"  eig(A + B K) = {eig}")
    lines.append(f"  spectral radius = {lqr['rho_Acl']:.12g}")
    lines.append("  stable? " + str(lqr["rho_Acl"] < 1.0))
    lines.append("")
    lines.append("Closed-loop tracking result")
    lines.append(f"  initial x = {case.x0}")
    lines.append(f"  final x = {sim['X'][-1]}")
    lines.append(f"  final y = {sim['Y'][-1]}")
    lines.append(f"  final r = {sim['Rvar'][-1]}")
    lines.append(f"  final u = {sim['U'][-1] if len(sim['U']) else np.array([])}")
    lines.append(f"  final ||x-xs|| = {sim['final_deviation_norm']:.12e}")
    lines.append(f"  final ||y-ysp|| = {sim['final_output_error_norm']:.12e}")
    lines.append(f"  final ||r-rsp|| = {sim['final_controlled_error_norm']:.12e}")
    lines.append("")
    lines.append("Selected simulation rows")
    idxs = sorted(set([0, 1, 2, 3, 5, 10, case.steps - 3, case.steps - 2, case.steps - 1, case.steps]))
    for k in idxs:
        if 0 <= k <= case.steps:
            u_text = sim["U"][k] if k < case.steps else "n/a"
            lines.append(
                f"  k={k:2d}: x={sim['X'][k]}, y={sim['Y'][k]}, "
                f"r={sim['Rvar'][k]}, u={u_text}, ||x-xs||={np.linalg.norm(sim['Xdev'][k]):.6g}"
            )
    if wrong is not None:
        lines.append("")
        lines.append("Intentional wrong comparison: regulating original x to zero")
        lines.append("  This ignores xs and us, so it solves the old regulation problem, not tracking.")
        lines.append(f"  final wrong-regulator y = {wrong['Y'][-1]}")
        lines.append(f"  desired ysp = {case.ysp}")
        lines.append(f"  wrong-regulator final output error = {np.linalg.norm(wrong['Y'][-1] - case.ysp):.12e}")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Case definitions
# ---------------------------------------------------------------------------


def build_cases() -> list[TrackingCase]:
    cases: list[TrackingCase] = []

    # Exact SISO tracking. Double integrator. Position target is feasible.
    A = np.array([[1.0, 1.0], [0.0, 1.0]])
    B = np.array([[0.5], [1.0]])
    C = np.array([[1.0, 0.0]])
    cases.append(TrackingCase(
        name="exact_siso_double_integrator",
        description=(
            "Exact SISO setpoint tracking. Output is position y=x1. "
            "The target ysp=10 is feasible with steady state xs=[10,0], us=0."
        ),
        A=A,
        B=B,
        C=C,
        H=np.eye(1),
        ysp=np.array([10.0]),
        rsp=np.array([10.0]),
        usp=np.array([0.0]),
        Qs=np.diag([20.0]),
        Rs=np.diag([1.0]),
        Qreg=np.diag([2.0, 0.4]),
        Rreg=np.diag([0.2]),
        x0=np.array([-4.0, 0.0]),
        steps=36,
    ))

    # More outputs than inputs. Track only a selected controlled variable r=H y.
    A = np.array([[0.70, 0.00], [0.00, 0.82]])
    B = np.array([[0.30], [0.12]])
    C = np.eye(2)
    cases.append(TrackingCase(
        name="more_outputs_than_inputs_controlled_variable",
        description=(
            "Two measured outputs and one input. We cannot generally force both outputs "
            "to arbitrary setpoints, so H selects controlled variable r=y1. "
            "The optimizer still penalizes y2-ysp2, but only r=y1 is imposed exactly."
        ),
        A=A,
        B=B,
        C=C,
        H=np.array([[1.0, 0.0]]),
        ysp=np.array([1.0, 2.0]),
        rsp=np.array([1.0]),
        usp=np.array([0.0]),
        Qs=np.diag([5.0, 5.0]),
        Rs=np.diag([0.2]),
        Qreg=np.diag([1.0, 1.0]),
        Rreg=np.diag([0.08]),
        x0=np.array([-1.0, -0.5]),
        steps=40,
    ))

    # More inputs than outputs. Same output target but input preference chooses one target among many.
    A = np.array([[0.80]])
    B = np.array([[0.20, 0.50]])
    C = np.array([[1.0]])
    cases.append(TrackingCase(
        name="more_inputs_than_outputs_input_preference",
        description=(
            "One measured output and two inputs. The output target y=1 has infinitely many "
            "steady input pairs. The input preference usp and Rs make us unique."
        ),
        A=A,
        B=B,
        C=C,
        H=np.eye(1),
        ysp=np.array([1.0]),
        rsp=np.array([1.0]),
        usp=np.array([0.0, 0.0]),
        Qs=np.diag([10.0]),
        Rs=np.diag([1.0, 1.0]),
        Qreg=np.diag([1.0]),
        Rreg=np.diag([0.2, 0.2]),
        x0=np.array([-0.5]),
        steps=32,
    ))

    cases.append(TrackingCase(
        name="more_inputs_than_outputs_prefer_u1",
        description=(
            "Same plant and output target as the previous case, but now the preferred input "
            "is usp=[1,0]. The target selector chooses a different us while still hitting y=1."
        ),
        A=A,
        B=B,
        C=C,
        H=np.eye(1),
        ysp=np.array([1.0]),
        rsp=np.array([1.0]),
        usp=np.array([1.0, 0.0]),
        Qs=np.diag([10.0]),
        Rs=np.diag([1.0, 1.0]),
        Qreg=np.diag([1.0]),
        Rreg=np.diag([0.2, 0.2]),
        x0=np.array([-0.5]),
        steps=32,
    ))

    return cases


def plot_input_preference_comparison(results: dict[str, dict[str, Any]], out_dir: Path) -> Path:
    a = results["more_inputs_than_outputs_input_preference"]
    b = results["more_inputs_than_outputs_prefer_u1"]
    target_a: TargetSolution = a["target"]
    target_b: TargetSolution = b["target"]
    sim_a = a["sim"]
    sim_b = b["sim"]

    fig, ax = plt.subplots(figsize=(8.5, 6.2))
    ax.scatter(target_a.us[0], target_a.us[1], s=90, label="target us for usp=[0,0]")
    ax.scatter(target_b.us[0], target_b.us[1], s=90, label="target us for usp=[1,0]")
    # Steady-state line for y=1: 0.2 = 0.2 u1 + 0.5 u2.
    u1 = np.linspace(-0.2, 1.3, 200)
    u2 = (0.2 - 0.2 * u1) / 0.5
    ax.plot(u1, u2, label="all steady inputs that give y=1")
    ax.scatter([0.0], [0.0], marker="x", s=80, label="usp=[0,0]")
    ax.scatter([1.0], [0.0], marker="x", s=80, label="usp=[1,0]")
    ax.set_title("More inputs than outputs: input preference selects the steady input")
    ax.set_xlabel("u1")
    ax.set_ylabel("u2")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path = out_dir / "input_preference_target_selector_map.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)

    # Also make an output comparison plot.
    fig, ax = plt.subplots(figsize=(10, 4.8))
    k = np.arange(sim_a["Y"].shape[0])
    ax.plot(k, sim_a["Y"][:, 0], label="y, target selected from usp=[0,0]")
    ax.plot(k, sim_b["Y"][:, 0], linestyle="--", label="y, target selected from usp=[1,0]")
    ax.axhline(1.0, linestyle=":", label="ysp=1")
    ax.set_title("Both input preferences track the same output setpoint")
    ax.set_xlabel("k")
    ax.set_ylabel("output y")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path2 = out_dir / "input_preference_output_comparison.png"
    fig.savefig(path2, dpi=160)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    out_dir = ensure_dir(script_dir / "out" / "tracking")

    cases = build_cases()
    results: dict[str, dict[str, Any]] = {}
    plot_paths: list[Path] = []
    log_parts: list[str] = []

    log_parts.append("Tracking - Calculation Log")
    log_parts.append("Rawlings / Mayne / Diehl Section 1.5.1 sandbox")
    log_parts.append("")
    log_parts.append("Core idea")
    log_parts.append("  Regulation to zero is not thrown away. It is reused after a coordinate shift.")
    log_parts.append("  First solve a target-selector problem for steady state (xs, us).")
    log_parts.append("  Then regulate xe = x - xs to zero with ue = u - us.")
    log_parts.append("  The actual plant input is u = us + ue.")
    log_parts.append("")

    for case in cases:
        target = solve_steady_state_target(case)
        sim = simulate_tracking(case, target)
        wrong = simulate_wrong_zero_regulator(case) if case.name == "exact_siso_double_integrator" else None
        results[case.name] = {"case": case, "target": target, "sim": sim, "wrong": wrong}

        write_csv(out_dir / f"{case.name}_simulation.csv", sim["rows"])
        plot_paths.extend(plot_case(case, target, sim, out_dir))
        if wrong is not None:
            plot_paths.append(plot_wrong_vs_shifted(case, target, sim, wrong, out_dir))
        log_parts.append(log_case(case, target, sim, wrong))

    plot_paths.append(plot_input_preference_comparison(results, out_dir))

    # Summary JSON.
    summary: dict[str, Any] = {"cases": {}}
    for name, bundle in results.items():
        case: TrackingCase = bundle["case"]
        target: TargetSolution = bundle["target"]
        sim = bundle["sim"]
        lqr = sim["lqr"]
        summary["cases"][name] = {
            "description": case.description,
            "A": case.A,
            "B": case.B,
            "C": case.C,
            "H": case.H,
            "ysp": case.ysp,
            "rsp": case.rsp,
            "usp": case.usp,
            "xs": target.xs,
            "us": target.us,
            "ys": target.ys,
            "rs": target.rs,
            "target_objective": target.objective,
            "equality_residual_norm": float(np.linalg.norm(target.equality_residual)),
            "rank_M": target.rank_M,
            "rank_augmented": target.rank_augmented,
            "feasible_equalities": target.feasible_equalities,
            "K": lqr["K"],
            "Acl": lqr["Acl"],
            "eig_Acl": lqr["eig_Acl"],
            "rho_Acl": lqr["rho_Acl"],
            "final_x": sim["X"][-1],
            "final_y": sim["Y"][-1],
            "final_r": sim["Rvar"][-1],
            "final_deviation_norm": sim["final_deviation_norm"],
            "final_output_error_norm": sim["final_output_error_norm"],
            "final_controlled_error_norm": sim["final_controlled_error_norm"],
        }

    json_path = out_dir / "tracking_summary.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(jsonable(summary), f, indent=2)
        f.write("\n")

    log_path = out_dir / "tracking_calculation_log.txt"
    log_path.write_text("\n".join(log_parts), encoding="utf-8")

    # Short README for output folder.
    readme_path = out_dir / "README_tracking_outputs.md"
    readme_path.write_text(
        "# Tracking sandbox outputs\n\n"
        "Generated by `tracking.py`.\n\n"
        "This sandbox follows Rawlings/Mayne/Diehl Section 1.5.1. It solves steady-state "
        "target-selector problems, shifts the system to deviation variables, and applies "
        "a zero-regulation LQR controller in those variables.\n\n"
        "Key files:\n\n"
        "- `tracking_calculation_log.txt`: detailed matrix calculations and interpretation.\n"
        "- `tracking_summary.json`: machine-readable summary.\n"
        "- `*_simulation.csv`: closed-loop data for each case.\n"
        "- `*.png`: output, input, state, and deviation-convergence plots.\n",
        encoding="utf-8",
    )

    # Zip all outputs for convenience.
    zip_path = script_dir / "tracking_outputs.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(out_dir.rglob("*")):
            if path.is_file():
                zf.write(path, arcname=str(path.relative_to(out_dir.parent)))

    print("Tracking sandbox complete.")
    print(f"Output directory: {out_dir}")
    print(f"Calculation log:  {log_path}")
    print(f"Summary JSON:     {json_path}")
    print(f"Output zip:       {zip_path}")
    print("Plots:")
    for p in plot_paths:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
