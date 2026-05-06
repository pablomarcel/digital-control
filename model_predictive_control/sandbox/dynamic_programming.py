#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
dynamic_programming.py

Sandbox for Rawlings/Mayne/Diehl Section 1.3.3: Dynamic Programming
Solution of the finite-horizon Linear Quadratic Regulator (LQR).

Purpose
-------
This script makes the Riccati iteration concrete. It shows that dynamic
programming is not magic: it is repeated completion of squares, working
backward from the terminal cost.

The model is the same simple discrete-time double integrator used in the
previous sandbox work:

    x(k+1) = A x(k) + B u(k)

where

    x1 = position
    x2 = velocity
    u  = acceleration command

For a finite horizon N, the cost is

    J = 1/2 sum_{k=0}^{N-1} [x(k)' Q x(k) + u(k)' R u(k)]
        + 1/2 x(N)' P_f x(N)

The dynamic-programming claim is that the optimal cost-to-go remains
quadratic:

    V_k(x) = 1/2 x' P_k x

and the matrices P_k are obtained by the backward Riccati recursion:

    P_k = Q + A' P_{k+1} A
          - A' P_{k+1} B (R + B' P_{k+1} B)^(-1) B' P_{k+1} A

The feedback gain at stage k is

    K_k = -(R + B' P_{k+1} B)^(-1) B' P_{k+1} A

and the optimal move is

    u(k) = K_k x(k)

Run examples
------------
From the repository root, package directory, or sandbox directory:

    python dynamic_programming.py
    python dynamic_programming.py --horizon 20 --x0 6 0 --show
    python dynamic_programming.py --horizon 8 --out-dir out/dynamic_programming

Outputs
-------
The script writes CSV files and MATLAB-style PNG plots:

    riccati_matrices.csv
    feedback_gains.csv
    closed_loop_trajectory.csv
    open_loop_optimal_plan.csv
    states_plot.png
    input_plot.png
    riccati_convergence_plot.png
    value_function_ellipses.png

Only NumPy and Matplotlib are required.
"""

from dataclasses import dataclass
from pathlib import Path
import argparse
import csv
import math
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class LQRProblem:
    """Finite-horizon discrete-time LQR problem data."""

    A: np.ndarray
    B: np.ndarray
    Q: np.ndarray
    R: np.ndarray
    Pf: np.ndarray
    N: int
    dt: float
    x0: np.ndarray
    state_names: tuple[str, ...]
    input_names: tuple[str, ...]

    @property
    def nx(self) -> int:
        return int(self.A.shape[0])

    @property
    def nu(self) -> int:
        return int(self.B.shape[1])


def make_double_integrator_problem(
    *,
    horizon: int = 15,
    dt: float = 0.1,
    x0: Iterable[float] = (6.0, 0.0),
    q_position: float = 8.0,
    q_velocity: float = 0.8,
    r_accel: float = 0.04,
    pf_position: float = 20.0,
    pf_velocity: float = 3.0,
) -> LQRProblem:
    """Create a discrete double-integrator finite-horizon LQR problem.

    The continuous intuition is:

        position_dot = velocity
        velocity_dot = acceleration

    Under zero-order-hold discretization with sample time dt:

        position(k+1) = position(k) + dt velocity(k) + 0.5 dt^2 u(k)
        velocity(k+1) = velocity(k) + dt u(k)
    """

    if horizon < 1:
        raise ValueError("horizon must be at least 1")
    if dt <= 0.0:
        raise ValueError("dt must be positive")

    A = np.array([[1.0, dt], [0.0, 1.0]], dtype=float)
    B = np.array([[0.5 * dt * dt], [dt]], dtype=float)
    Q = np.diag([q_position, q_velocity]).astype(float)
    R = np.array([[r_accel]], dtype=float)
    Pf = np.diag([pf_position, pf_velocity]).astype(float)
    x0_arr = np.asarray(tuple(x0), dtype=float)
    if x0_arr.shape != (2,):
        raise ValueError("x0 must contain exactly two values: position velocity")

    return LQRProblem(
        A=A,
        B=B,
        Q=Q,
        R=R,
        Pf=Pf,
        N=int(horizon),
        dt=float(dt),
        x0=x0_arr,
        state_names=("position", "velocity"),
        input_names=("acceleration_command",),
    )


def riccati_backward(problem: LQRProblem) -> tuple[list[np.ndarray], list[np.ndarray]]:
    """Compute P_k and K_k with the backward Riccati recursion.

    Returns
    -------
    P:
        List of length N + 1. P[k] is the cost-to-go matrix at stage k.
    K:
        List of length N. K[k] maps x(k) to u(k): u(k) = K[k] x(k).
    """

    A, B, Q, R, Pf, N = problem.A, problem.B, problem.Q, problem.R, problem.Pf, problem.N

    P: list[np.ndarray] = [np.zeros_like(Q) for _ in range(N + 1)]
    K: list[np.ndarray] = [np.zeros((problem.nu, problem.nx)) for _ in range(N)]

    P[N] = Pf.copy()
    for k in range(N - 1, -1, -1):
        S = R + B.T @ P[k + 1] @ B
        K[k] = -np.linalg.solve(S, B.T @ P[k + 1] @ A)
        P[k] = Q + A.T @ P[k + 1] @ A + A.T @ P[k + 1] @ B @ K[k]
        P[k] = 0.5 * (P[k] + P[k].T)  # remove tiny roundoff asymmetry

    return P, K


def rollout_feedback(problem: LQRProblem, K: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Roll the system forward using the time-varying optimal feedback gains."""

    X = np.zeros((problem.N + 1, problem.nx), dtype=float)
    U = np.zeros((problem.N, problem.nu), dtype=float)
    stage_cost = np.zeros(problem.N + 1, dtype=float)

    X[0] = problem.x0
    for k in range(problem.N):
        U[k] = K[k] @ X[k]
        stage_cost[k] = 0.5 * (X[k].T @ problem.Q @ X[k] + U[k].T @ problem.R @ U[k])
        X[k + 1] = problem.A @ X[k] + problem.B @ U[k]
    stage_cost[-1] = 0.5 * X[-1].T @ problem.Pf @ X[-1]
    return X, U, stage_cost


def build_condensed_prediction_matrices(problem: LQRProblem) -> tuple[np.ndarray, np.ndarray]:
    """Build X = M x0 + G U for simultaneous open-loop optimization.

    This is included as a sanity check. It solves the same finite-horizon
    problem in one large linear algebra step, then compares against the
    Riccati / DP result.
    """

    N, nx, nu = problem.N, problem.nx, problem.nu
    A, B = problem.A, problem.B

    M = np.zeros(((N + 1) * nx, nx), dtype=float)
    G = np.zeros(((N + 1) * nx, N * nu), dtype=float)

    for i in range(N + 1):
        M[i * nx : (i + 1) * nx, :] = np.linalg.matrix_power(A, i)
        for j in range(i):
            G[i * nx : (i + 1) * nx, j * nu : (j + 1) * nu] = np.linalg.matrix_power(A, i - 1 - j) @ B

    return M, G


def solve_condensed_open_loop(problem: LQRProblem) -> tuple[np.ndarray, np.ndarray, float]:
    """Solve the finite-horizon LQR by one simultaneous quadratic program.

    Since this sandbox is unconstrained, the QP has a closed-form solution.
    The solution is used to prove that the Riccati recursion is producing the
    same optimal input sequence.
    """

    N, nx, nu = problem.N, problem.nx, problem.nu
    M, G = build_condensed_prediction_matrices(problem)

    Qbar = np.zeros(((N + 1) * nx, (N + 1) * nx), dtype=float)
    for k in range(N):
        Qbar[k * nx : (k + 1) * nx, k * nx : (k + 1) * nx] = problem.Q
    Qbar[N * nx : (N + 1) * nx, N * nx : (N + 1) * nx] = problem.Pf

    Rbar = np.kron(np.eye(N), problem.R)
    H = G.T @ Qbar @ G + Rbar
    g = G.T @ Qbar @ M @ problem.x0

    U_flat = -np.linalg.solve(H, g)
    X_flat = M @ problem.x0 + G @ U_flat
    U = U_flat.reshape(N, nu)
    X = X_flat.reshape(N + 1, nx)
    cost = 0.5 * (X_flat.T @ Qbar @ X_flat + U_flat.T @ Rbar @ U_flat)
    return X, U, float(cost)


def cost_from_trajectory(problem: LQRProblem, X: np.ndarray, U: np.ndarray) -> float:
    """Evaluate the finite-horizon LQR objective for a trajectory."""

    total = 0.0
    for k in range(problem.N):
        total += 0.5 * float(X[k].T @ problem.Q @ X[k] + U[k].T @ problem.R @ U[k])
    total += 0.5 * float(X[-1].T @ problem.Pf @ X[-1])
    return total


def value_function(problem: LQRProblem, P: list[np.ndarray], k: int, x: np.ndarray) -> float:
    """Return V_k(x) = 1/2 x' P_k x."""

    return 0.5 * float(x.T @ P[k] @ x)


def one_step_completion_of_squares_demo(problem: LQRProblem, P_next: np.ndarray, x: np.ndarray) -> dict[str, np.ndarray | float]:
    """Show the local one-step minimization that produces K.

    Given V_{k+1}(x_next) = 1/2 x_next' P_next x_next, minimize

        1/2 x'Qx + 1/2 u'Ru + 1/2(Ax+Bu)'P_next(Ax+Bu)

    with respect to u. The minimizer is u = Kx.
    """

    A, B, Q, R = problem.A, problem.B, problem.Q, problem.R
    S = R + B.T @ P_next @ B
    F = B.T @ P_next @ A
    K = -np.linalg.solve(S, F)
    u_star = K @ x

    def local_cost(u: np.ndarray) -> float:
        x_next = A @ x + B @ u
        return 0.5 * float(x.T @ Q @ x + u.T @ R @ u + x_next.T @ P_next @ x_next)

    return {
        "S": S,
        "F": F,
        "K": K,
        "x": x,
        "u_star": u_star,
        "local_cost_at_u_star": local_cost(u_star),
        "local_cost_at_zero_u": local_cost(np.zeros(problem.nu)),
        "local_cost_at_positive_u": local_cost(np.array([1.0])),
        "local_cost_at_negative_u": local_cost(np.array([-1.0])),
    }


def write_csv(path: Path, header: list[str], rows: Iterable[Iterable[float | int | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def save_outputs(problem: LQRProblem, P: list[np.ndarray], K: list[np.ndarray], X: np.ndarray, U: np.ndarray, X_open: np.ndarray, U_open: np.ndarray, out_dir: Path, show: bool = False) -> dict[str, Path]:
    """Save CSV and plots."""

    out_dir.mkdir(parents=True, exist_ok=True)
    files: dict[str, Path] = {}

    riccati_rows = []
    for k, Pk in enumerate(P):
        riccati_rows.append([k, Pk[0, 0], Pk[0, 1], Pk[1, 0], Pk[1, 1], np.linalg.det(Pk), max(np.linalg.eigvals(Pk).real)])
    files["riccati_csv"] = out_dir / "riccati_matrices.csv"
    write_csv(files["riccati_csv"], ["k", "P11", "P12", "P21", "P22", "det_P", "max_eig_P"], riccati_rows)

    gain_rows = []
    for k, Kk in enumerate(K):
        gain_rows.append([k, Kk[0, 0], Kk[0, 1]])
    files["gains_csv"] = out_dir / "feedback_gains.csv"
    write_csv(files["gains_csv"], ["k", "K_position", "K_velocity"], gain_rows)

    state_rows = []
    for k in range(problem.N + 1):
        u = U[k, 0] if k < problem.N else ""
        state_rows.append([k, k * problem.dt, X[k, 0], X[k, 1], u])
    files["closed_loop_csv"] = out_dir / "closed_loop_trajectory.csv"
    write_csv(files["closed_loop_csv"], ["k", "time", "position", "velocity", "acceleration_command"], state_rows)

    open_rows = []
    for k in range(problem.N + 1):
        u = U_open[k, 0] if k < problem.N else ""
        open_rows.append([k, k * problem.dt, X_open[k, 0], X_open[k, 1], u])
    files["open_loop_csv"] = out_dir / "open_loop_optimal_plan.csv"
    write_csv(files["open_loop_csv"], ["k", "time", "position", "velocity", "acceleration_command"], open_rows)

    import matplotlib.pyplot as plt

    time_x = np.arange(problem.N + 1) * problem.dt
    time_u = np.arange(problem.N) * problem.dt

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(time_x, X[:, 0], marker="o", label="position")
    ax.plot(time_x, X[:, 1], marker="s", label="velocity")
    ax.axhline(0.0, linewidth=1.0)
    ax.set_title("Finite-horizon LQR via dynamic programming - states")
    ax.set_xlabel("time")
    ax.set_ylabel("state")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    fig.tight_layout()
    files["states_plot"] = out_dir / "states_plot.png"
    fig.savefig(files["states_plot"], dpi=160)
    if show:
        plt.show()
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.step(time_u, U[:, 0], where="post", label="u = acceleration command")
    ax.axhline(0.0, linewidth=1.0)
    ax.set_title("Optimal control input sequence")
    ax.set_xlabel("time")
    ax.set_ylabel("input")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    fig.tight_layout()
    files["input_plot"] = out_dir / "input_plot.png"
    fig.savefig(files["input_plot"], dpi=160)
    if show:
        plt.show()
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5.2))
    k_grid = np.arange(problem.N + 1)
    ax.plot(k_grid, [Pk[0, 0] for Pk in P], marker="o", label="P11: position cost-to-go weight")
    ax.plot(k_grid, [Pk[0, 1] for Pk in P], marker="s", label="P12/P21: coupling weight")
    ax.plot(k_grid, [Pk[1, 1] for Pk in P], marker="^", label="P22: velocity cost-to-go weight")
    ax.invert_xaxis()
    ax.set_title("Backward Riccati recursion: P_N to P_0")
    ax.set_xlabel("stage k (right-to-left is backward time)")
    ax.set_ylabel("matrix entry")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    files["riccati_plot"] = out_dir / "riccati_convergence_plot.png"
    fig.savefig(files["riccati_plot"], dpi=160)
    if show:
        plt.show()
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 6.4))
    theta = np.linspace(0.0, 2.0 * math.pi, 300)
    unit = np.vstack([np.cos(theta), np.sin(theta)])
    levels = [(0, "V0(x)=10"), (problem.N // 2, f"V{problem.N // 2}(x)=10"), (problem.N, f"V{problem.N}(x)=10")]
    for k, label in levels:
        Pk = P[k]
        vals, vecs = np.linalg.eigh(Pk)
        vals = np.maximum(vals, 1e-12)
        radius = np.sqrt(2.0 * 10.0 / vals)
        ellipse = vecs @ (radius.reshape(2, 1) * unit)
        ax.plot(ellipse[0], ellipse[1], label=label)
    ax.scatter([problem.x0[0]], [problem.x0[1]], marker="x", s=80, label="x0")
    ax.set_title("Cost-to-go ellipses: V_k(x) = 1/2 x' P_k x")
    ax.set_xlabel("position")
    ax.set_ylabel("velocity")
    ax.grid(True, alpha=0.3)
    ax.axis("equal")
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    files["ellipses_plot"] = out_dir / "value_function_ellipses.png"
    fig.savefig(files["ellipses_plot"], dpi=160)
    if show:
        plt.show()
    plt.close(fig)

    return files


def print_matrix(name: str, M: np.ndarray) -> None:
    """Pretty-print a small matrix."""

    print(f"{name} =")
    with np.printoptions(precision=6, suppress=True):
        print(M)


def run(args: argparse.Namespace) -> int:
    problem = make_double_integrator_problem(
        horizon=args.horizon,
        dt=args.dt,
        x0=args.x0,
        q_position=args.q_position,
        q_velocity=args.q_velocity,
        r_accel=args.r_accel,
        pf_position=args.pf_position,
        pf_velocity=args.pf_velocity,
    )

    P, K = riccati_backward(problem)
    X, U, stage_cost = rollout_feedback(problem, K)
    dp_cost = cost_from_trajectory(problem, X, U)
    value_cost = value_function(problem, P, 0, problem.x0)
    X_open, U_open, condensed_cost = solve_condensed_open_loop(problem)

    demo = one_step_completion_of_squares_demo(problem, P[1], problem.x0)

    out_dir = Path(args.out_dir).expanduser().resolve()
    files = save_outputs(problem, P, K, X, U, X_open, U_open, out_dir, show=args.show)

    print("\nDynamic Programming / Riccati sandbox complete")
    print("=" * 60)
    print("System: discrete double integrator")
    print("States: x1 = position, x2 = velocity")
    print("Input : u = acceleration command")
    print(f"Horizon N = {problem.N}")
    print(f"Sample time dt = {problem.dt}")
    print_matrix("A", problem.A)
    print_matrix("B", problem.B)
    print_matrix("Q", problem.Q)
    print_matrix("R", problem.R)
    print_matrix("Pf", problem.Pf)

    print("\nRiccati idea in one sentence:")
    print("  start at terminal cost P_N = Pf, then move backward and ask:")
    print("  if tomorrow's cost is 1/2 x' P_{k+1} x, what is today's best u?")

    print("\nFirst few backward objects")
    print("-" * 60)
    print_matrix("P_N", P[-1])
    print_matrix("P_0", P[0])
    print_matrix("K_0", K[0])
    if problem.N > 1:
        print_matrix("K_1", K[1])
    print_matrix("K_{N-1}", K[-1])

    print("\nOne-step completion-of-squares demo at k=0")
    print("-" * 60)
    print_matrix("S = R + B' P_1 B", np.asarray(demo["S"]))
    print_matrix("F = B' P_1 A", np.asarray(demo["F"]))
    print_matrix("K = -S^{-1} F", np.asarray(demo["K"]))
    print_matrix("x0", np.asarray(demo["x"]))
    print_matrix("u* = K x0", np.asarray(demo["u_star"]))
    print(f"local cost at u*  : {demo['local_cost_at_u_star']:.8f}")
    print(f"local cost at u=0 : {demo['local_cost_at_zero_u']:.8f}")
    print(f"local cost at u=+1: {demo['local_cost_at_positive_u']:.8f}")
    print(f"local cost at u=-1: {demo['local_cost_at_negative_u']:.8f}")

    print("\nSanity checks")
    print("-" * 60)
    print(f"Cost from closed-loop DP rollout       : {dp_cost:.10f}")
    print(f"Value function V0(x0) = 1/2 x0'P0x0   : {value_cost:.10f}")
    print(f"Cost from simultaneous open-loop solve : {condensed_cost:.10f}")
    print(f"max |U_DP - U_open_loop|               : {np.max(np.abs(U - U_open)):.3e}")
    print(f"max |X_DP - X_open_loop|               : {np.max(np.abs(X - X_open)):.3e}")

    print("\nFinal state after applying all finite-horizon gains")
    print("-" * 60)
    print_matrix("x_N", X[-1])
    print(f"total stage + terminal cost: {stage_cost.sum():.10f}")

    print("\nFiles")
    print("-" * 60)
    for label, path in files.items():
        print(f"{label:<18}: {path}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sandbox Rawlings Section 1.3.3 dynamic programming / Riccati iteration.",
    )
    parser.add_argument("--horizon", type=int, default=15, help="Finite horizon N")
    parser.add_argument("--dt", type=float, default=0.1, help="Sample time")
    parser.add_argument("--x0", type=float, nargs=2, default=(6.0, 0.0), metavar=("POSITION", "VELOCITY"), help="Initial state")
    parser.add_argument("--q-position", type=float, default=8.0, help="Q weight on position")
    parser.add_argument("--q-velocity", type=float, default=0.8, help="Q weight on velocity")
    parser.add_argument("--r-accel", type=float, default=0.04, help="R weight on acceleration command")
    parser.add_argument("--pf-position", type=float, default=20.0, help="Terminal weight on position")
    parser.add_argument("--pf-velocity", type=float, default=3.0, help="Terminal weight on velocity")
    parser.add_argument("--out-dir", default="out/dynamic_programming", help="Output directory for CSV and plots")
    parser.add_argument("--show", action="store_true", help="Show Matplotlib figures interactively")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
