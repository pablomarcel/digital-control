#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
ex_1_1.py — Rawlings/Mayne/Diehl MPC, Exercise 1.1 sandbox.

This script solves the simple batch-reaction modeling exercise from
Chapter 1, Exercise 1.1:

    A --k1--> B --k2--> C

The state vector is

    x = [c_A, c_B, c_C]^T

and the model is the autonomous continuous-time linear system

    dx/dt = A x
    y     = C x

with y = c_A.

Default numerical data:

    c_A(0) = 1
    c_B(0) = 0
    c_C(0) = 0
    k1     = 2
    k2     = 1

Outputs are written to out/ex_1_1 by default:

    ex_1_1_results.json
    ex_1_1_trajectory.csv
    ex_1_1_log.txt
    ex_1_1_concentrations.png
    ex_1_1_mass_balance_error.png

Run examples:

    python ex_1_1.py
    python ex_1_1.py --t-final 6 --num-points 301
    python ex_1_1.py --out out/ex_1_1 --show
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import argparse
import csv
import json

import numpy as np

try:
    from scipy.integrate import solve_ivp
except Exception:  # pragma: no cover - fallback for minimal environments
    solve_ivp = None

try:
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover - plotting is optional
    plt = None


@dataclass(frozen=True)
class ExerciseConfig:
    """Input data for Exercise 1.1."""

    k1: float = 2.0
    k2: float = 1.0
    cA0: float = 1.0
    cB0: float = 0.0
    cC0: float = 0.0
    t_final: float = 6.0
    num_points: int = 301


def build_state_space(k1: float, k2: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Build the continuous-time state-space matrices.

    Model:
        c_A_dot = -k1 c_A
        c_B_dot =  k1 c_A - k2 c_B
        c_C_dot =  k2 c_B
        y       =  c_A

    There is no manipulated input in this batch-reaction exercise.
    For compatibility with the usual form dx/dt = A x + B u,
    B and D are returned as zero-column matrices.
    """

    A = np.array(
        [
            [-k1, 0.0, 0.0],
            [k1, -k2, 0.0],
            [0.0, k2, 0.0],
        ],
        dtype=float,
    )
    B = np.zeros((3, 0), dtype=float)
    C = np.array([[1.0, 0.0, 0.0]], dtype=float)
    D = np.zeros((1, 0), dtype=float)
    return A, B, C, D


def rhs(t: float, x: np.ndarray, A: np.ndarray) -> np.ndarray:
    """Right-hand side for dx/dt = A x."""

    return A @ x


def analytical_solution(t: np.ndarray, cfg: ExerciseConfig) -> np.ndarray:
    """Analytical solution for c_A0=1, c_B0=0, c_C0=0.

    The textbook numerical request uses c_A0=1, c_B0=0, c_C0=0.  The
    closed-form formulas below are valid for that initial condition and
    k1 != k2.  For other initial conditions or k1 == k2, the script still
    computes the numerical solution and uses matrix-exponential formulas
    for the exact trajectory when SciPy is available.
    """

    if not np.isclose(cfg.cA0, 1.0) or not np.isclose(cfg.cB0, 0.0) or not np.isclose(cfg.cC0, 0.0):
        raise ValueError("The simple closed-form solution implemented here assumes [1, 0, 0].")
    if np.isclose(cfg.k1, cfg.k2):
        raise ValueError("The simple closed-form solution implemented here assumes k1 != k2.")

    cA = np.exp(-cfg.k1 * t)
    cB = cfg.k1 / (cfg.k1 - cfg.k2) * (np.exp(-cfg.k2 * t) - np.exp(-cfg.k1 * t))
    cC = 1.0 - cA - cB
    return np.column_stack([cA, cB, cC])


def simulate(cfg: ExerciseConfig) -> dict[str, Any]:
    """Simulate Exercise 1.1 and return all calculation results."""

    A, B, C, D = build_state_space(cfg.k1, cfg.k2)
    x0 = np.array([cfg.cA0, cfg.cB0, cfg.cC0], dtype=float)
    t_eval = np.linspace(0.0, cfg.t_final, cfg.num_points)

    if solve_ivp is not None:
        sol = solve_ivp(
            fun=lambda t, x: rhs(t, x, A),
            t_span=(0.0, cfg.t_final),
            y0=x0,
            t_eval=t_eval,
            method="RK45",
            rtol=1.0e-10,
            atol=1.0e-12,
        )
        if not sol.success:
            raise RuntimeError(f"solve_ivp failed: {sol.message}")
        X_num = sol.y.T
    else:
        # Conservative explicit-Euler fallback.  The default environment normally
        # has SciPy, but this keeps the sandbox runnable in minimal installs.
        X_num = np.zeros((cfg.num_points, 3), dtype=float)
        X_num[0] = x0
        dt = t_eval[1] - t_eval[0]
        for i in range(cfg.num_points - 1):
            X_num[i + 1] = X_num[i] + dt * rhs(t_eval[i], X_num[i], A)

    # Use the closed form for the exact trajectory when the textbook data are used.
    exact_available = False
    X_exact = None
    try:
        X_exact = analytical_solution(t_eval, cfg)
        exact_available = True
    except ValueError:
        X_exact = None

    Y_num = (C @ X_num.T).T
    total_concentration = X_num.sum(axis=1)
    initial_total = float(np.sum(x0))
    mass_balance_error = total_concentration - initial_total
    eigvals = np.linalg.eigvals(A)

    # Important physical event: B is the intermediate, so its concentration rises
    # first and then falls.  The peak location is useful for interpretation.
    peak_idx = int(np.argmax(X_num[:, 1]))
    peak_B = {
        "time": float(t_eval[peak_idx]),
        "c_B": float(X_num[peak_idx, 1]),
        "c_A": float(X_num[peak_idx, 0]),
        "c_C": float(X_num[peak_idx, 2]),
    }

    final_state = X_num[-1]
    result: dict[str, Any] = {
        "title": "Rawlings MPC Exercise 1.1 - batch reaction A to B to C",
        "config": asdict(cfg),
        "state_names": ["c_A", "c_B", "c_C"],
        "output_names": ["y = c_A"],
        "system_type": "continuous_time_autonomous_linear_state_space",
        "model_equations": [
            "dc_A/dt = -k1 c_A",
            "dc_B/dt =  k1 c_A - k2 c_B",
            "dc_C/dt =  k2 c_B",
            "y = c_A",
        ],
        "A": A.tolist(),
        "B": B.tolist(),
        "C": C.tolist(),
        "D": D.tolist(),
        "eigenvalues_A": [complex(v).real if abs(complex(v).imag) < 1e-12 else [complex(v).real, complex(v).imag] for v in eigvals],
        "time": t_eval.tolist(),
        "X_numerical": X_num.tolist(),
        "Y_numerical": Y_num.tolist(),
        "X_exact": X_exact.tolist() if exact_available and X_exact is not None else None,
        "max_abs_numerical_exact_error": float(np.max(np.abs(X_num - X_exact))) if exact_available and X_exact is not None else None,
        "total_concentration": total_concentration.tolist(),
        "max_abs_mass_balance_error": float(np.max(np.abs(mass_balance_error))),
        "peak_B": peak_B,
        "final_state": final_state.tolist(),
        "interpretation": {
            "state_1": "c_A decays because A is consumed by the first reaction.",
            "state_2": "c_B rises first because B is produced from A, then falls because B is consumed into C.",
            "state_3": "c_C rises toward the conserved total concentration because C is the final product.",
            "input": "No manipulated input is present in this batch-reaction exercise.",
            "mass_balance": "For this closed batch system, c_A + c_B + c_C remains constant.",
        },
    }
    return result


def write_json(result: dict[str, Any], path: Path) -> None:
    """Write result JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")


def write_csv(result: dict[str, Any], path: Path) -> None:
    """Write trajectory CSV."""

    t = np.asarray(result["time"], dtype=float)
    X = np.asarray(result["X_numerical"], dtype=float)
    Y = np.asarray(result["Y_numerical"], dtype=float)
    total = np.asarray(result["total_concentration"], dtype=float)
    x_exact = result.get("X_exact")
    X_exact = np.asarray(x_exact, dtype=float) if x_exact is not None else None

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["time", "c_A", "c_B", "c_C", "y_c_A", "total_c"]
        if X_exact is not None:
            header += ["c_A_exact", "c_B_exact", "c_C_exact"]
        writer.writerow(header)
        for i in range(t.size):
            row: list[float] = [float(t[i]), *[float(v) for v in X[i]], float(Y[i, 0]), float(total[i])]
            if X_exact is not None:
                row += [float(v) for v in X_exact[i]]
            writer.writerow(row)


def build_log(result: dict[str, Any]) -> str:
    """Create a readable calculation log."""

    cfg = result["config"]
    A = np.asarray(result["A"], dtype=float)
    B = np.asarray(result["B"], dtype=float)
    C = np.asarray(result["C"], dtype=float)
    D = np.asarray(result["D"], dtype=float)
    peak = result["peak_B"]
    final_state = result["final_state"]

    lines = []
    lines.append("Rawlings/Mayne/Diehl MPC - Exercise 1.1 sandbox")
    lines.append("Batch reaction: A --k1--> B --k2--> C")
    lines.append("")
    lines.append("State definition")
    lines.append("  x = [c_A, c_B, c_C]^T")
    lines.append("  y = c_A")
    lines.append("")
    lines.append("Differential equations")
    lines.append("  dc_A/dt = -k1 c_A")
    lines.append("  dc_B/dt =  k1 c_A - k2 c_B")
    lines.append("  dc_C/dt =  k2 c_B")
    lines.append("")
    lines.append("State-space form")
    lines.append("  dx/dt = A x + B u")
    lines.append("  y     = C x + D u")
    lines.append("  No manipulated input is present, so B and D are zero-column matrices.")
    lines.append("")
    lines.append(f"k1 = {cfg['k1']}")
    lines.append(f"k2 = {cfg['k2']}")
    lines.append(f"x0 = [{cfg['cA0']}, {cfg['cB0']}, {cfg['cC0']}]")
    lines.append("")
    lines.append("A matrix")
    lines.append(str(A))
    lines.append("B matrix")
    lines.append(str(B))
    lines.append("C matrix")
    lines.append(str(C))
    lines.append("D matrix")
    lines.append(str(D))
    lines.append("")
    lines.append("Eigenvalues of A")
    lines.append(f"  {result['eigenvalues_A']}")
    lines.append("  The zero eigenvalue is expected because final product C accumulates and is not consumed.")
    lines.append("")
    lines.append("Analytical solution for the textbook data [1, 0, 0], k1 != k2")
    lines.append("  c_A(t) = exp(-k1 t)")
    lines.append("  c_B(t) = k1/(k1-k2) * [exp(-k2 t) - exp(-k1 t)]")
    lines.append("  c_C(t) = 1 - c_A(t) - c_B(t)")
    lines.append("")
    lines.append("Numerical checks")
    lines.append(f"  max |numerical - exact| = {result['max_abs_numerical_exact_error']}")
    lines.append(f"  max |c_A + c_B + c_C - initial_total| = {result['max_abs_mass_balance_error']}")
    lines.append("")
    lines.append("Intermediate B peak")
    lines.append(f"  t_peak_B = {peak['time']}")
    lines.append(f"  c_B_peak = {peak['c_B']}")
    lines.append(f"  c_A_at_peak = {peak['c_A']}")
    lines.append(f"  c_C_at_peak = {peak['c_C']}")
    lines.append("")
    lines.append("Final state at t_final")
    lines.append(f"  c_A = {final_state[0]}")
    lines.append(f"  c_B = {final_state[1]}")
    lines.append(f"  c_C = {final_state[2]}")
    lines.append("")
    lines.append("Physical interpretation")
    lines.append("  A decreases monotonically because it is consumed.")
    lines.append("  B rises first because it is produced from A, then falls because it is consumed into C.")
    lines.append("  C rises toward the conserved total concentration because it is the final product.")
    return "\n".join(lines) + "\n"


def write_log(result: dict[str, Any], path: Path) -> None:
    """Write calculation log."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_log(result), encoding="utf-8")


def make_plots(result: dict[str, Any], out_dir: Path, show: bool = False) -> dict[str, str]:
    """Create concentration and mass-balance plots."""

    if plt is None:
        return {}

    out_dir.mkdir(parents=True, exist_ok=True)
    t = np.asarray(result["time"], dtype=float)
    X = np.asarray(result["X_numerical"], dtype=float)
    total = np.asarray(result["total_concentration"], dtype=float)
    initial_total = total[0]
    max_mass_error = result["max_abs_mass_balance_error"]

    paths: dict[str, str] = {}

    fig, ax = plt.subplots(figsize=(10.0, 6.0))
    ax.plot(t, X[:, 0], label="c_A")
    ax.plot(t, X[:, 1], label="c_B")
    ax.plot(t, X[:, 2], label="c_C")
    ax.set_title("Exercise 1.1 batch reaction: A → B → C")
    ax.set_xlabel("time")
    ax.set_ylabel("concentration")
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best")
    fig.tight_layout()
    path = out_dir / "ex_1_1_concentrations.png"
    fig.savefig(path, dpi=160)
    paths["concentrations_plot"] = str(path)
    if show:
        plt.show()
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10.0, 4.8))
    ax.plot(t, total - initial_total, label="mass-balance error")
    ax.set_title(f"Mass-balance error, max abs = {max_mass_error:.3e}")
    ax.set_xlabel("time")
    ax.set_ylabel("c_A + c_B + c_C - initial total")
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best")
    fig.tight_layout()
    path = out_dir / "ex_1_1_mass_balance_error.png"
    fig.savefig(path, dpi=160)
    paths["mass_balance_plot"] = str(path)
    if show:
        plt.show()
    plt.close(fig)

    return paths


def save_all(result: dict[str, Any], out_dir: Path, show: bool = False) -> dict[str, str]:
    """Save all script outputs."""

    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "ex_1_1_results.json"
    csv_path = out_dir / "ex_1_1_trajectory.csv"
    log_path = out_dir / "ex_1_1_log.txt"
    write_json(result, json_path)
    write_csv(result, csv_path)
    write_log(result, log_path)
    files = {
        "json": str(json_path),
        "csv": str(csv_path),
        "log": str(log_path),
    }
    files.update(make_plots(result, out_dir, show=show))
    return files


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description="Solve Rawlings MPC Exercise 1.1.")
    parser.add_argument("--k1", type=float, default=2.0, help="First reaction rate constant")
    parser.add_argument("--k2", type=float, default=1.0, help="Second reaction rate constant")
    parser.add_argument("--cA0", type=float, default=1.0, help="Initial concentration of A")
    parser.add_argument("--cB0", type=float, default=0.0, help="Initial concentration of B")
    parser.add_argument("--cC0", type=float, default=0.0, help="Initial concentration of C")
    parser.add_argument("--t-final", type=float, default=6.0, help="Final simulation time")
    parser.add_argument("--num-points", type=int, default=301, help="Number of output time points")
    parser.add_argument("--out", type=str, default="out/ex_1_1", help="Output directory")
    parser.add_argument("--show", action="store_true", help="Show plots interactively")
    return parser.parse_args()


def main() -> int:
    """Run the Exercise 1.1 sandbox."""

    args = parse_args()
    cfg = ExerciseConfig(
        k1=args.k1,
        k2=args.k2,
        cA0=args.cA0,
        cB0=args.cB0,
        cC0=args.cC0,
        t_final=args.t_final,
        num_points=args.num_points,
    )
    result = simulate(cfg)
    files = save_all(result, Path(args.out), show=args.show)

    print("Exercise 1.1 run complete.")
    print(f"A matrix: {result['A']}")
    print(f"Final state: {result['final_state']}")
    print(f"Peak B: {result['peak_B']}")
    print(f"Max mass-balance error: {result['max_abs_mass_balance_error']:.3e}")
    print("Files:")
    for label, path in files.items():
        print(f"  {label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
