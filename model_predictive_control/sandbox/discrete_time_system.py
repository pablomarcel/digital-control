#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
rawlings_eq_1_4_sandbox.py

Standalone sandbox for Rawlings, Mayne, and Diehl, Section 1.2.4,
Equation (1.4): the analytical solution of the discrete-time LTI model

    x(k+1) = A x(k) + B u(k)
    y(k)   = C x(k) + D u(k)
    x(0)   = x0

Equation (1.4) gives

    x(k) = A^k x0 + sum_{j=0}^{k-1} A^(k-j-1) B u(j)

This script compares two equivalent ways to generate the trajectory:

1. recursive simulation:
       x[k+1] = A @ x[k] + B @ u[k]

2. analytical/convolution-sum formula:
       x[k] = A^k @ x0 + sum(A^(k-j-1) @ B @ u[j])

The point of the sandbox is not MPC optimization yet. It is simply to
understand how the model predicts state values x(k) once A, B, C, D,
x0, and an input sequence u(k) are given.

Run examples:

    python rawlings_eq_1_4_sandbox.py
    python rawlings_eq_1_4_sandbox.py --steps 80 --input-profile step --plot
    python rawlings_eq_1_4_sandbox.py --system scalar --input-profile sine --plot
    python rawlings_eq_1_4_sandbox.py --system unstable --input-profile zero --plot

Outputs are written by default to ./out/rawlings_eq_1_4_sandbox/
"""

from dataclasses import dataclass
from pathlib import Path
import argparse
import csv
import json
from typing import Callable

import numpy as np


@dataclass(frozen=True)
class LTIDiscreteSystem:
    """Container for a finite-dimensional, discrete-time LTI system."""

    A: np.ndarray
    B: np.ndarray
    C: np.ndarray
    D: np.ndarray
    x0: np.ndarray
    dt: float = 1.0
    name: str = "lti_discrete_system"

    @property
    def nx(self) -> int:
        return int(self.A.shape[0])

    @property
    def nu(self) -> int:
        return int(self.B.shape[1])

    @property
    def ny(self) -> int:
        return int(self.C.shape[0])


def validate_system(sys: LTIDiscreteSystem) -> None:
    """Validate matrix dimensions before running the sandbox."""

    A, B, C, D, x0 = sys.A, sys.B, sys.C, sys.D, sys.x0
    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise ValueError(f"A must be square; got {A.shape}")
    if B.ndim != 2 or B.shape[0] != A.shape[0]:
        raise ValueError(f"B must have shape (nx, nu); got {B.shape}")
    if C.ndim != 2 or C.shape[1] != A.shape[0]:
        raise ValueError(f"C must have shape (ny, nx); got {C.shape}")
    if D.ndim != 2 or D.shape != (C.shape[0], B.shape[1]):
        raise ValueError(f"D must have shape (ny, nu); got {D.shape}")
    if x0.ndim != 1 or x0.shape[0] != A.shape[0]:
        raise ValueError(f"x0 must have shape (nx,); got {x0.shape}")
    for name, arr in {"A": A, "B": B, "C": C, "D": D, "x0": x0}.items():
        if not np.all(np.isfinite(arr)):
            raise ValueError(f"{name} contains non-finite values")


def example_system(name: str = "double_integrator", dt: float = 0.1) -> LTIDiscreteSystem:
    """Return one of several small systems useful for sandboxing equation (1.4)."""

    key = name.strip().lower().replace("-", "_")

    if key in {"double_integrator", "di"}:
        # Same conceptual plant as the package's MPC demo:
        # x1 = position, x2 = velocity, u = acceleration command.
        A = np.array([[1.0, dt], [0.0, 1.0]], dtype=float)
        B = np.array([[0.5 * dt * dt], [dt]], dtype=float)
        C = np.eye(2)
        D = np.zeros((2, 1))
        x0 = np.array([0.0, 0.0], dtype=float)
        return LTIDiscreteSystem(A=A, B=B, C=C, D=D, x0=x0, dt=dt, name="double_integrator")

    if key in {"stable", "stable_2state"}:
        A = np.array([[0.88, 0.18], [-0.08, 0.78]], dtype=float)
        B = np.array([[0.10], [0.06]], dtype=float)
        C = np.eye(2)
        D = np.zeros((2, 1))
        x0 = np.array([2.0, -1.0], dtype=float)
        return LTIDiscreteSystem(A=A, B=B, C=C, D=D, x0=x0, dt=dt, name="stable_2state")

    if key in {"unstable", "unstable_2state"}:
        A = np.array([[1.08, 0.10], [0.0, 1.03]], dtype=float)
        B = np.array([[0.05], [0.10]], dtype=float)
        C = np.eye(2)
        D = np.zeros((2, 1))
        x0 = np.array([0.5, 0.0], dtype=float)
        return LTIDiscreteSystem(A=A, B=B, C=C, D=D, x0=x0, dt=dt, name="unstable_2state")

    if key in {"scalar", "first_order"}:
        A = np.array([[0.90]], dtype=float)
        B = np.array([[0.20]], dtype=float)
        C = np.array([[1.0]], dtype=float)
        D = np.array([[0.0]], dtype=float)
        x0 = np.array([1.0], dtype=float)
        return LTIDiscreteSystem(A=A, B=B, C=C, D=D, x0=x0, dt=dt, name="scalar_first_order")

    raise ValueError(
        f"Unknown system {name!r}. Use double_integrator, stable, unstable, or scalar."
    )


def make_input_sequence(
    profile: str,
    steps: int,
    nu: int,
    *,
    dt: float = 1.0,
    amplitude: float = 1.0,
) -> np.ndarray:
    """Create u(k) for k = 0, ..., steps - 1."""

    key = profile.strip().lower().replace("-", "_")
    U = np.zeros((steps, nu), dtype=float)
    t = np.arange(steps, dtype=float) * dt

    if key == "zero":
        return U
    if key == "step":
        U[:, :] = amplitude
        return U
    if key == "pulse":
        width = max(1, steps // 5)
        start = max(0, steps // 10)
        U[start : start + width, :] = amplitude
        return U
    if key == "sine":
        values = amplitude * np.sin(2.0 * np.pi * t / max(dt, steps * dt / 4.0))
        U[:, :] = values.reshape(-1, 1)
        return U
    if key == "ramp":
        values = amplitude * np.linspace(0.0, 1.0, steps)
        U[:, :] = values.reshape(-1, 1)
        return U
    if key == "alternating":
        values = amplitude * np.where(np.arange(steps) % 2 == 0, 1.0, -1.0)
        U[:, :] = values.reshape(-1, 1)
        return U

    raise ValueError(
        f"Unknown input profile {profile!r}. Use zero, step, pulse, sine, ramp, or alternating."
    )


def simulate_recursive(sys: LTIDiscreteSystem, U: np.ndarray) -> np.ndarray:
    """Compute x(k) by direct recurrence x(k+1) = A x(k) + B u(k)."""

    steps = U.shape[0]
    X = np.zeros((steps + 1, sys.nx), dtype=float)
    X[0] = sys.x0
    for k in range(steps):
        X[k + 1] = sys.A @ X[k] + sys.B @ U[k]
    return X


def analytical_state_at_k(sys: LTIDiscreteSystem, U: np.ndarray, k: int) -> np.ndarray:
    """Compute x(k) from Rawlings equation (1.4)."""

    if k < 0 or k > U.shape[0]:
        raise ValueError(f"k must satisfy 0 <= k <= steps; got {k}")

    # Initial-condition contribution: A^k x0.
    xk = np.linalg.matrix_power(sys.A, k) @ sys.x0

    # Forced response contribution: sum_{j=0}^{k-1} A^(k-j-1) B u(j).
    for j in range(k):
        xk = xk + np.linalg.matrix_power(sys.A, k - j - 1) @ sys.B @ U[j]
    return xk


def simulate_analytical(sys: LTIDiscreteSystem, U: np.ndarray) -> np.ndarray:
    """Compute the full x(k) trajectory using equation (1.4)."""

    steps = U.shape[0]
    X = np.zeros((steps + 1, sys.nx), dtype=float)
    for k in range(steps + 1):
        X[k] = analytical_state_at_k(sys, U, k)
    return X


def output_trajectory(sys: LTIDiscreteSystem, X: np.ndarray, U: np.ndarray) -> np.ndarray:
    """Compute y(k) = C x(k) + D u(k) for k = 0, ..., steps - 1."""

    steps = U.shape[0]
    Y = np.zeros((steps, sys.ny), dtype=float)
    for k in range(steps):
        Y[k] = sys.C @ X[k] + sys.D @ U[k]
    return Y


def build_prediction_matrix(sys: LTIDiscreteSystem, steps: int) -> tuple[np.ndarray, np.ndarray]:
    """Build condensed matrices Phi and Gamma such that X_stack = Phi x0 + Gamma U_stack.

    X_stack contains x(1), x(2), ..., x(steps). This is the same analytical
    solution reorganized as one large matrix multiplication. This condensed
    form is a preview of what MPC/QP implementations later exploit.
    """

    nx, nu = sys.nx, sys.nu
    Phi = np.zeros((steps * nx, nx), dtype=float)
    Gamma = np.zeros((steps * nx, steps * nu), dtype=float)

    for row_k in range(1, steps + 1):
        row = slice((row_k - 1) * nx, row_k * nx)
        Phi[row, :] = np.linalg.matrix_power(sys.A, row_k)
        for j in range(row_k):
            col = slice(j * nu, (j + 1) * nu)
            Gamma[row, col] = np.linalg.matrix_power(sys.A, row_k - j - 1) @ sys.B

    return Phi, Gamma


def simulate_condensed(sys: LTIDiscreteSystem, U: np.ndarray) -> np.ndarray:
    """Compute the trajectory using the condensed prediction matrix form."""

    steps = U.shape[0]
    Phi, Gamma = build_prediction_matrix(sys, steps)
    stacked = Phi @ sys.x0 + Gamma @ U.reshape(-1)
    X = np.zeros((steps + 1, sys.nx), dtype=float)
    X[0] = sys.x0
    X[1:] = stacked.reshape(steps, sys.nx)
    return X


def write_csv(path: Path, sys: LTIDiscreteSystem, U: np.ndarray, X: np.ndarray, Y: np.ndarray) -> None:
    """Write time, input, state, and output trajectories to CSV."""

    path.parent.mkdir(parents=True, exist_ok=True)
    steps = U.shape[0]
    header = (
        ["k", "time"]
        + [f"x{i + 1}" for i in range(sys.nx)]
        + [f"u{i + 1}" for i in range(sys.nu)]
        + [f"y{i + 1}" for i in range(sys.ny)]
    )
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for k in range(steps):
            writer.writerow([k, k * sys.dt, *X[k], *U[k], *Y[k]])
        writer.writerow([(steps), steps * sys.dt, *X[-1], *([np.nan] * sys.nu), *([np.nan] * sys.ny)])


def write_json(path: Path, payload: dict) -> None:
    """Write a JSON result file with NumPy arrays converted to lists."""

    def convert(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.floating, np.integer)):
            return obj.item()
        if isinstance(obj, Path):
            return str(obj)
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=convert)
        f.write("\n")


def plot_trajectories(path: Path, sys: LTIDiscreteSystem, U: np.ndarray, X: np.ndarray, Y: np.ndarray) -> None:
    """Create a simple Matplotlib figure for the sandbox results."""

    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    t_x = np.arange(X.shape[0], dtype=float) * sys.dt
    t_u = np.arange(U.shape[0], dtype=float) * sys.dt

    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=False)

    ax = axes[0]
    for i in range(sys.nx):
        ax.plot(t_x, X[:, i], marker="o", markersize=2.5, label=f"x{i + 1}")
    ax.set_title(f"State trajectory from Rawlings equation (1.4): {sys.name}")
    ax.set_xlabel("time")
    ax.set_ylabel("state")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")

    ax = axes[1]
    for i in range(sys.nu):
        ax.step(t_u, U[:, i], where="post", label=f"u{i + 1}")
    ax.set_title("Input sequence")
    ax.set_xlabel("time")
    ax.set_ylabel("input")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")

    ax = axes[2]
    for i in range(sys.ny):
        ax.plot(t_u, Y[:, i], marker=".", markersize=3.0, label=f"y{i + 1}")
    ax.set_title("Output trajectory")
    ax.set_xlabel("time")
    ax.set_ylabel("output")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")

    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def spectral_summary(A: np.ndarray) -> dict:
    """Return eigenvalues and spectral radius of A."""

    eig = np.linalg.eigvals(A)
    return {
        "eigenvalues": eig,
        "spectral_radius": float(np.max(np.abs(eig))),
        "discrete_time_stability_hint": "stable if spectral_radius < 1; marginal if near 1; unstable if > 1",
    }


def run_sandbox(args: argparse.Namespace) -> dict:
    """Run the selected sandbox case and save artifacts."""

    sys = example_system(args.system, dt=args.dt)
    validate_system(sys)

    if args.x0 is not None:
        x0 = np.array([float(v) for v in args.x0.split(",")], dtype=float)
        sys = LTIDiscreteSystem(A=sys.A, B=sys.B, C=sys.C, D=sys.D, x0=x0, dt=sys.dt, name=sys.name)
        validate_system(sys)

    U = make_input_sequence(
        args.input_profile,
        args.steps,
        sys.nu,
        dt=sys.dt,
        amplitude=args.amplitude,
    )

    X_recursive = simulate_recursive(sys, U)
    X_analytical = simulate_analytical(sys, U)
    X_condensed = simulate_condensed(sys, U)
    Y = output_trajectory(sys, X_analytical, U)

    max_err_recursive_vs_analytical = float(np.max(np.abs(X_recursive - X_analytical)))
    max_err_condensed_vs_analytical = float(np.max(np.abs(X_condensed - X_analytical)))

    out_dir = Path(args.out_dir).expanduser().resolve()
    stem = f"{sys.name}_{args.input_profile}"
    csv_path = out_dir / f"{stem}.csv"
    json_path = out_dir / f"{stem}.json"
    plot_path = out_dir / f"{stem}.png"

    write_csv(csv_path, sys, U, X_analytical, Y)

    result = {
        "title": "Rawlings Section 1.2.4 Equation (1.4) sandbox",
        "system_name": sys.name,
        "steps": args.steps,
        "dt": sys.dt,
        "A": sys.A,
        "B": sys.B,
        "C": sys.C,
        "D": sys.D,
        "x0": sys.x0,
        "input_profile": args.input_profile,
        "U": U,
        "X_recursive": X_recursive,
        "X_analytical_eq_1_4": X_analytical,
        "X_condensed_prediction_matrix": X_condensed,
        "Y": Y,
        "max_abs_error_recursive_vs_analytical": max_err_recursive_vs_analytical,
        "max_abs_error_condensed_vs_analytical": max_err_condensed_vs_analytical,
        "spectral_summary": spectral_summary(sys.A),
        "files": {"csv": csv_path, "json": json_path, "plot": plot_path if args.plot else None},
    }
    write_json(json_path, result)

    if args.plot:
        plot_trajectories(plot_path, sys, U, X_analytical, Y)

    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sandbox Rawlings MPC Section 1.2.4, equation (1.4)."
    )
    parser.add_argument(
        "--system",
        default="double_integrator",
        help="Example system: double_integrator, stable, unstable, scalar",
    )
    parser.add_argument("--steps", type=int, default=40, help="Number of input samples")
    parser.add_argument("--dt", type=float, default=0.1, help="Sample time")
    parser.add_argument(
        "--input-profile",
        default="step",
        help="Input profile: zero, step, pulse, sine, ramp, alternating",
    )
    parser.add_argument("--amplitude", type=float, default=1.0, help="Input amplitude")
    parser.add_argument(
        "--x0",
        default=None,
        help="Optional comma-separated initial state override, e.g. '6,0'",
    )
    parser.add_argument(
        "--out-dir",
        default="out/discrete_time_system",
        help="Output directory for CSV/JSON/plot files",
    )
    parser.add_argument("--plot", action="store_true", help="Save a PNG plot")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.steps < 1:
        parser.error("--steps must be at least 1")
    if args.dt <= 0:
        parser.error("--dt must be positive")

    result = run_sandbox(args)

    print("Rawlings equation (1.4) sandbox complete.")
    print(f"  system                         : {result['system_name']}")
    print(f"  input_profile                  : {result['input_profile']}")
    print(f"  steps                          : {result['steps']}")
    print(f"  final_state                    : {np.asarray(result['X_analytical_eq_1_4'])[-1]}")
    print(f"  spectral_radius(A)             : {result['spectral_summary']['spectral_radius']:.6g}")
    print(f"  recursive vs analytical error  : {result['max_abs_error_recursive_vs_analytical']:.3e}")
    print(f"  condensed vs analytical error  : {result['max_abs_error_condensed_vs_analytical']:.3e}")
    print("  files:")
    for label, path in result["files"].items():
        if path is not None:
            print(f"    {label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
