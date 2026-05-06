#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
convergence_lqr_sandbox.py

Sandbox for Rawlings, Mayne, and Diehl, Section 1.3.6:
Convergence of the Linear Quadratic Regulator.

The script intentionally writes to:

    out/convergence_lqr

by default, matching the project convention.

What this sandbox calculates/tests
----------------------------------
1. Controllability prerequisite for the example system.
2. Finite-horizon Riccati iterations for the page 21/22 example.
3. Closed-loop eigenvalues of A + B K_N as the horizon grows.
4. Infinite-horizon DARE solution Pi and feedback gain K_inf.
5. Closed-loop stability test: spectral radius(A + B K_inf) < 1.
6. Lyapunov/cost-to-go decrease from Lemma 1.3:

       V(x+) - V(x) = -0.5 * (x'Qx + u'Ru)

   for the infinite-horizon LQR law u = K_inf x.
7. Closed-loop simulations comparing N=5, N=7, and infinite-horizon LQR.

Run examples
------------
From the package root or repo root:

    python sandbox/convergence_lqr_sandbox.py

or from wherever the file lives:

    python convergence_lqr_sandbox.py

Optional output override:

    python convergence_lqr_sandbox.py --out out/convergence_lqr
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import argparse
import csv
import json
import math

import numpy as np


# -----------------------------------------------------------------------------
# Small serialization and formatting helpers
# -----------------------------------------------------------------------------


def jsonable(value: Any) -> Any:
    """Convert NumPy/complex-heavy values into JSON-safe objects."""

    if isinstance(value, np.ndarray):
        return jsonable(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, Path):
        return str(value)
    return value


def fmt_float(x: float, digits: int = 10) -> str:
    """Compact floating-point formatter for reports."""

    if not math.isfinite(float(x)):
        return str(x)
    return f"{float(x):.{digits}g}"


def fmt_complex(z: complex, digits: int = 10) -> str:
    """Compact complex-number formatter for reports."""

    z = complex(z)
    if abs(z.imag) < 1e-12:
        return fmt_float(z.real, digits)
    sign = "+" if z.imag >= 0 else "-"
    return f"{fmt_float(z.real, digits)} {sign} {fmt_float(abs(z.imag), digits)}j"


def matrix_to_text(M: np.ndarray, digits: int = 10) -> str:
    """Return a readable matrix block."""

    arr = np.asarray(M)
    rows = []
    for row in arr:
        cells = []
        for v in row:
            if np.iscomplexobj(arr):
                cells.append(fmt_complex(complex(v), digits))
            else:
                cells.append(fmt_float(float(v), digits))
        rows.append("[" + ", ".join(cells) + "]")
    return "\n".join(rows)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(jsonable(data), f, indent=2)
        f.write("\n")


# -----------------------------------------------------------------------------
# Control calculations
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class LQRSystem:
    name: str
    A: np.ndarray
    B: np.ndarray
    Q: np.ndarray
    R: np.ndarray
    Pf: np.ndarray


@dataclass(frozen=True)
class GainRecord:
    horizon: int
    K: np.ndarray
    P: np.ndarray
    eig_closed_loop: np.ndarray
    spectral_radius: float
    stable: bool
    K_error_to_inf: float | None = None
    P_error_to_inf: float | None = None


def rawlings_page_21_system() -> LQRSystem:
    """Return the unstable-zero LQ example from pages 21 and 22."""

    A = np.array([[4.0 / 3.0, -2.0 / 3.0], [1.0, 0.0]], dtype=float)
    B = np.array([[1.0], [0.0]], dtype=float)
    C = np.array([[-2.0 / 3.0, 1.0]], dtype=float)
    Q = C.T @ C + 0.001 * np.eye(2)
    R = np.array([[0.001]], dtype=float)
    Pf = Q.copy()
    return LQRSystem(
        name="Rawlings page 21/22 unstable-zero LQ example",
        A=A,
        B=B,
        Q=Q,
        R=R,
        Pf=Pf,
    )


def controllability_matrix(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Build C = [B, AB, ..., A^(n-1)B]."""

    n = A.shape[0]
    blocks = []
    Ak = np.eye(n)
    for _ in range(n):
        blocks.append(Ak @ B)
        Ak = Ak @ A
    return np.hstack(blocks)


def matrix_rank(M: np.ndarray, tol: float = 1e-9) -> int:
    """Numerical matrix rank using SVD and an explicit tolerance."""

    s = np.linalg.svd(np.asarray(M), compute_uv=False)
    return int(np.sum(s > tol))


def lqr_gain_from_P(A: np.ndarray, B: np.ndarray, R: np.ndarray, P_next: np.ndarray) -> np.ndarray:
    """Compute K = -(B' P B + R)^(-1) B' P A."""

    S = B.T @ P_next @ B + R
    return -np.linalg.solve(S, B.T @ P_next @ A)


def riccati_update(A: np.ndarray, B: np.ndarray, Q: np.ndarray, R: np.ndarray, P_next: np.ndarray) -> np.ndarray:
    """One Riccati recursion/update."""

    S = B.T @ P_next @ B + R
    return Q + A.T @ P_next @ A - A.T @ P_next @ B @ np.linalg.solve(S, B.T @ P_next @ A)


def finite_horizon_gain(system: LQRSystem, horizon: int) -> tuple[np.ndarray, np.ndarray]:
    """Return the first finite-horizon gain K_N(0) and P_0.

    The book example starts with terminal P_f = Q and iterates the Riccati
    equation horizon - 1 times before computing the first gain. This reproduces
    the page 21/22 numbers:

    N=5 -> eig(A+B K_5(0)) approximately {1.307, 0.001}
    N=7 -> eig(A+B K_7(0)) approximately {0.989, 0.001}
    """

    if horizon < 1:
        raise ValueError("horizon must be >= 1")

    P = system.Pf.copy()
    for _ in range(horizon - 1):
        P = riccati_update(system.A, system.B, system.Q, system.R, P)
    K = lqr_gain_from_P(system.A, system.B, system.R, P)
    return K, P


def solve_dare_iterative(
    A: np.ndarray,
    B: np.ndarray,
    Q: np.ndarray,
    R: np.ndarray,
    *,
    P0: np.ndarray | None = None,
    max_iter: int = 10000,
    tol: float = 1e-12,
) -> tuple[np.ndarray, int, float]:
    """Solve the DARE by fixed-point Riccati iteration."""

    P = Q.copy() if P0 is None else np.asarray(P0, dtype=float).copy()
    err = float("inf")
    for i in range(1, max_iter + 1):
        P_next = riccati_update(A, B, Q, R, P)
        err = float(np.linalg.norm(P_next - P, ord="fro"))
        P = P_next
        if err < tol:
            return P, i, err
    return P, max_iter, err


def solve_dare(system: LQRSystem) -> tuple[np.ndarray, str, int | None, float | None]:
    """Solve DARE using SciPy when available, otherwise Riccati iteration."""

    try:
        from scipy.linalg import solve_discrete_are  # type: ignore

        P = np.asarray(solve_discrete_are(system.A, system.B, system.Q, system.R), dtype=float)
        return P, "scipy.linalg.solve_discrete_are", None, None
    except Exception:
        P, iterations, err = solve_dare_iterative(system.A, system.B, system.Q, system.R)
        return P, "fixed-point Riccati iteration fallback", iterations, err


def closed_loop_record(system: LQRSystem, horizon: int, P_inf: np.ndarray, K_inf: np.ndarray) -> GainRecord:
    """Build a finite-horizon record and compare it to infinite-horizon values."""

    K, P = finite_horizon_gain(system, horizon)
    eig = np.linalg.eigvals(system.A + system.B @ K)
    rho = float(np.max(np.abs(eig)))
    return GainRecord(
        horizon=horizon,
        K=K,
        P=P,
        eig_closed_loop=eig,
        spectral_radius=rho,
        stable=bool(rho < 1.0),
        K_error_to_inf=float(np.linalg.norm(K - K_inf, ord="fro")),
        P_error_to_inf=float(np.linalg.norm(P - P_inf, ord="fro")),
    )


def simulate_closed_loop(
    A: np.ndarray,
    B: np.ndarray,
    K: np.ndarray,
    x0: np.ndarray,
    steps: int,
    Q: np.ndarray | None = None,
    R: np.ndarray | None = None,
    P: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """Simulate x+ = (A + BK)x and optionally log Lyapunov values."""

    n = A.shape[0]
    m = B.shape[1]
    X = np.zeros((steps + 1, n), dtype=float)
    U = np.zeros((steps, m), dtype=float)
    norms = np.zeros(steps + 1, dtype=float)
    V = np.full(steps + 1, np.nan, dtype=float)
    stage = np.full(steps, np.nan, dtype=float)
    delta = np.full(steps, np.nan, dtype=float)
    lyap_residual = np.full(steps, np.nan, dtype=float)

    X[0] = np.asarray(x0, dtype=float).reshape(-1)
    norms[0] = float(np.linalg.norm(X[0]))
    if P is not None:
        V[0] = 0.5 * float(X[0].T @ P @ X[0])

    for k in range(steps):
        U[k] = K @ X[k]
        X[k + 1] = A @ X[k] + B @ U[k]
        norms[k + 1] = float(np.linalg.norm(X[k + 1]))
        if Q is not None and R is not None and P is not None:
            stage[k] = 0.5 * float(X[k].T @ Q @ X[k] + U[k].T @ R @ U[k])
            V[k + 1] = 0.5 * float(X[k + 1].T @ P @ X[k + 1])
            delta[k] = V[k + 1] - V[k]
            lyap_residual[k] = delta[k] + stage[k]

    return {
        "X": X,
        "U": U,
        "state_norm": norms,
        "V": V,
        "stage_cost": stage,
        "delta_V": delta,
        "lyapunov_residual": lyap_residual,
    }


# -----------------------------------------------------------------------------
# Output writers
# -----------------------------------------------------------------------------


def write_riccati_csv(path: Path, records: list[GainRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "horizon_N",
            "K_0_0",
            "K_0_1",
            "eig_1_real",
            "eig_1_imag",
            "eig_2_real",
            "eig_2_imag",
            "spectral_radius",
            "stable_rho_lt_1",
            "K_error_to_K_inf_fro",
            "P_error_to_P_inf_fro",
        ])
        for r in records:
            eig = list(r.eig_closed_loop)
            while len(eig) < 2:
                eig.append(complex(float("nan"), 0.0))
            writer.writerow([
                r.horizon,
                *[f"{v:.16g}" for v in r.K.reshape(-1)[:2]],
                f"{eig[0].real:.16g}",
                f"{eig[0].imag:.16g}",
                f"{eig[1].real:.16g}",
                f"{eig[1].imag:.16g}",
                f"{r.spectral_radius:.16g}",
                int(r.stable),
                f"{r.K_error_to_inf:.16g}" if r.K_error_to_inf is not None else "",
                f"{r.P_error_to_inf:.16g}" if r.P_error_to_inf is not None else "",
            ])


def write_trajectory_csv(path: Path, simulations: dict[str, dict[str, np.ndarray]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    max_steps = max(sim["X"].shape[0] for sim in simulations.values()) - 1
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "case",
            "k",
            "x1",
            "x2",
            "u",
            "state_norm",
            "V_inf",
            "stage_cost",
            "delta_V",
            "lyapunov_residual_delta_plus_stage",
        ])
        for name, sim in simulations.items():
            X = sim["X"]
            U = sim["U"]
            for k in range(max_steps + 1):
                if k >= X.shape[0]:
                    continue
                u = U[k, 0] if k < U.shape[0] else float("nan")
                stage = sim["stage_cost"][k] if k < sim["stage_cost"].shape[0] else float("nan")
                delta = sim["delta_V"][k] if k < sim["delta_V"].shape[0] else float("nan")
                residual = sim["lyapunov_residual"][k] if k < sim["lyapunov_residual"].shape[0] else float("nan")
                writer.writerow([
                    name,
                    k,
                    f"{X[k, 0]:.16g}",
                    f"{X[k, 1]:.16g}",
                    f"{u:.16g}",
                    f"{sim['state_norm'][k]:.16g}",
                    f"{sim['V'][k]:.16g}",
                    f"{stage:.16g}",
                    f"{delta:.16g}",
                    f"{residual:.16g}",
                ])


def make_plots(out_dir: Path, records: list[GainRecord], simulations: dict[str, dict[str, np.ndarray]]) -> dict[str, str]:
    """Create plots if matplotlib is available."""

    try:
        import matplotlib.pyplot as plt
    except Exception:
        return {}

    paths: dict[str, str] = {}

    horizons = np.array([r.horizon for r in records], dtype=float)
    rho = np.array([r.spectral_radius for r in records], dtype=float)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(horizons, rho, marker="o")
    ax.axhline(1.0, linestyle="--", linewidth=1)
    ax.set_title("Closed-loop spectral radius versus Riccati horizon")
    ax.set_xlabel("horizon N")
    ax.set_ylabel("spectral radius of A + B K_N(0)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    path = out_dir / "spectral_radius_vs_horizon.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    paths["spectral_radius_plot"] = str(path)

    fig, ax = plt.subplots(figsize=(9, 5))
    for name, sim in simulations.items():
        ax.semilogy(np.arange(sim["state_norm"].shape[0]), sim["state_norm"], label=name)
    ax.set_title("Closed-loop state norm")
    ax.set_xlabel("k")
    ax.set_ylabel("||x(k)||")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path = out_dir / "state_norm_vs_time.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    paths["state_norm_plot"] = str(path)

    if "infinite_horizon" in simulations:
        sim = simulations["infinite_horizon"]
        fig, ax = plt.subplots(figsize=(9, 5))
        k = np.arange(sim["delta_V"].shape[0])
        ax.plot(k, sim["delta_V"], label="delta V")
        ax.plot(k, -sim["stage_cost"], linestyle="--", label="-stage cost")
        ax.set_title("Infinite-horizon LQR Lyapunov decrease check")
        ax.set_xlabel("k")
        ax.set_ylabel("value")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best", fontsize=8)
        fig.tight_layout()
        path = out_dir / "lyapunov_decrease_check.png"
        fig.savefig(path, dpi=160)
        plt.close(fig)
        paths["lyapunov_plot"] = str(path)

    return paths


def write_report(
    path: Path,
    system: LQRSystem,
    controllability: dict[str, Any],
    P_inf: np.ndarray,
    K_inf: np.ndarray,
    dare_source: str,
    dare_iterations: int | None,
    dare_error: float | None,
    infinite_eig: np.ndarray,
    infinite_rho: float,
    records: list[GainRecord],
    simulations: dict[str, dict[str, np.ndarray]],
    plot_paths: dict[str, str],
) -> None:
    """Write a Markdown report."""

    path.parent.mkdir(parents=True, exist_ok=True)

    def eig_list(eig: np.ndarray) -> str:
        return ", ".join(fmt_complex(complex(v)) for v in eig)

    rec5 = next((r for r in records if r.horizon == 5), None)
    rec7 = next((r for r in records if r.horizon == 7), None)

    lines: list[str] = []
    lines.append("# LQR Convergence Sandbox Report")
    lines.append("")
    lines.append("This report was generated by `convergence_lqr_sandbox.py`.")
    lines.append("")
    lines.append("The output directory is intentionally named `out/convergence_lqr`.")
    lines.append("")
    lines.append("## Section 1.3.6 theory checks implemented")
    lines.append("")
    lines.append("- Build the page 21/22 LQ example system.")
    lines.append("- Confirm the controllability prerequisite used by Lemma 1.3.")
    lines.append("- Iterate the Riccati equation for increasing finite horizons.")
    lines.append("- Compute each finite-horizon first feedback gain `K_N(0)`.")
    lines.append("- Compute `eig(A + B K_N(0))` and the spectral radius.")
    lines.append("- Solve the infinite-horizon DARE for `Pi` and `K_inf`.")
    lines.append("- Test infinite-horizon stability with `rho(A + B K_inf) < 1`.")
    lines.append("- Check the Lyapunov/cost-to-go decrease used in the proof:")
    lines.append("  `V(x+) - V(x) = -0.5*(x'Qx + u'Ru)`.")
    lines.append("")

    lines.append("## System")
    lines.append("")
    lines.append(f"- name: `{system.name}`")
    lines.append(f"- n states: `{system.A.shape[0]}`")
    lines.append(f"- m inputs: `{system.B.shape[1]}`")
    lines.append(f"- open-loop eigenvalues of A: {eig_list(np.linalg.eigvals(system.A))}")
    lines.append(f"- controllability rank: `{controllability['rank']}` / required `{system.A.shape[0]}`")
    lines.append(f"- controllable: `{controllability['controllable']}`")
    lines.append("")
    lines.append("### A")
    lines.append("")
    lines.append("```text")
    lines.append(matrix_to_text(system.A))
    lines.append("```")
    lines.append("")
    lines.append("### B")
    lines.append("")
    lines.append("```text")
    lines.append(matrix_to_text(system.B))
    lines.append("```")
    lines.append("")
    lines.append("### Q")
    lines.append("")
    lines.append("```text")
    lines.append(matrix_to_text(system.Q))
    lines.append("```")
    lines.append("")
    lines.append("### R")
    lines.append("")
    lines.append("```text")
    lines.append(matrix_to_text(system.R))
    lines.append("```")
    lines.append("")
    lines.append("### Controllability matrix C")
    lines.append("")
    lines.append("```text")
    lines.append(matrix_to_text(controllability["matrix"]))
    lines.append("```")
    lines.append("")

    lines.append("## Finite-horizon Riccati checks")
    lines.append("")
    lines.append("The page 21/22 warning is reproduced here: a short finite-horizon LQ gain can be unstable even with Q > 0 and R > 0.")
    lines.append("")
    if rec5 is not None:
        lines.append("### N = 5")
        lines.append("")
        lines.append(f"- K_5(0): `{matrix_to_text(rec5.K).replace(chr(10), '; ')}`")
        lines.append(f"- eig(A + B K_5(0)): {eig_list(rec5.eig_closed_loop)}")
        lines.append(f"- spectral radius: `{fmt_float(rec5.spectral_radius)}`")
        lines.append(f"- stable: `{rec5.stable}`")
        lines.append("")
    if rec7 is not None:
        lines.append("### N = 7")
        lines.append("")
        lines.append(f"- K_7(0): `{matrix_to_text(rec7.K).replace(chr(10), '; ')}`")
        lines.append(f"- eig(A + B K_7(0)): {eig_list(rec7.eig_closed_loop)}")
        lines.append(f"- spectral radius: `{fmt_float(rec7.spectral_radius)}`")
        lines.append(f"- stable: `{rec7.stable}`")
        lines.append("")

    lines.append("## Infinite-horizon DARE result")
    lines.append("")
    lines.append(f"- DARE solver: `{dare_source}`")
    if dare_iterations is not None:
        lines.append(f"- DARE iterations: `{dare_iterations}`")
    if dare_error is not None:
        lines.append(f"- final DARE iteration error: `{fmt_float(dare_error)}`")
    lines.append(f"- eig(A + B K_inf): {eig_list(infinite_eig)}")
    lines.append(f"- spectral radius: `{fmt_float(infinite_rho)}`")
    lines.append(f"- stable/convergent: `{infinite_rho < 1.0}`")
    lines.append("")
    lines.append("### Pi")
    lines.append("")
    lines.append("```text")
    lines.append(matrix_to_text(P_inf))
    lines.append("```")
    lines.append("")
    lines.append("### K_inf")
    lines.append("")
    lines.append("```text")
    lines.append(matrix_to_text(K_inf))
    lines.append("```")
    lines.append("")

    lines.append("## Lyapunov decrease check")
    lines.append("")
    sim_inf = simulations["infinite_horizon"]
    max_resid = float(np.nanmax(np.abs(sim_inf["lyapunov_residual"])))
    monotone = bool(np.all(np.diff(sim_inf["V"]) <= 1e-9))
    lines.append(f"- max absolute residual in `delta_V + stage_cost`: `{fmt_float(max_resid)}`")
    lines.append(f"- V_inf(x(k)) monotone nonincreasing: `{monotone}`")
    lines.append(f"- initial state norm: `{fmt_float(sim_inf['state_norm'][0])}`")
    lines.append(f"- final state norm: `{fmt_float(sim_inf['state_norm'][-1])}`")
    lines.append("")
    lines.append("Interpretation: the infinite-horizon value function behaves like a Lyapunov function. Each step consumes a positive stage cost, so the value function drops until the state approaches the origin.")
    lines.append("")

    lines.append("## Generated files")
    lines.append("")
    lines.append("- `lqr_convergence_results.json`")
    lines.append("- `riccati_iteration_log.csv`")
    lines.append("- `closed_loop_trajectory.csv`")
    lines.append("- `lqr_convergence_report.md`")
    for label, p in plot_paths.items():
        lines.append(f"- `{Path(p).name}` ({label})")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


# -----------------------------------------------------------------------------
# Main orchestration
# -----------------------------------------------------------------------------


def run(out_dir: Path, steps: int = 40) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)

    system = rawlings_page_21_system()
    Cmat = controllability_matrix(system.A, system.B)
    crank = matrix_rank(Cmat)
    controllability = {
        "matrix": Cmat,
        "rank": crank,
        "required_rank": system.A.shape[0],
        "controllable": bool(crank == system.A.shape[0]),
    }

    P_inf, dare_source, dare_iterations, dare_error = solve_dare(system)
    K_inf = lqr_gain_from_P(system.A, system.B, system.R, P_inf)
    Acl_inf = system.A + system.B @ K_inf
    eig_inf = np.linalg.eigvals(Acl_inf)
    rho_inf = float(np.max(np.abs(eig_inf)))

    records = [closed_loop_record(system, N, P_inf, K_inf) for N in range(1, 41)]

    K5, _ = finite_horizon_gain(system, 5)
    K7, _ = finite_horizon_gain(system, 7)

    x0 = np.array([1.0, 1.0], dtype=float)
    simulations = {
        "finite_horizon_N5_fixed_gain": simulate_closed_loop(system.A, system.B, K5, x0, steps),
        "finite_horizon_N7_fixed_gain": simulate_closed_loop(system.A, system.B, K7, x0, steps),
        "infinite_horizon": simulate_closed_loop(
            system.A,
            system.B,
            K_inf,
            x0,
            steps,
            Q=system.Q,
            R=system.R,
            P=P_inf,
        ),
    }

    write_riccati_csv(out_dir / "riccati_iteration_log.csv", records)
    write_trajectory_csv(out_dir / "closed_loop_trajectory.csv", simulations)
    plot_paths = make_plots(out_dir, records, simulations)

    result = {
        "title": "Section 1.3.6 LQR convergence sandbox",
        "output_directory": str(out_dir),
        "system": {
            "name": system.name,
            "A": system.A,
            "B": system.B,
            "Q": system.Q,
            "R": system.R,
            "Pf": system.Pf,
            "open_loop_eigenvalues": np.linalg.eigvals(system.A),
        },
        "controllability": controllability,
        "dare": {
            "solver": dare_source,
            "iterations": dare_iterations,
            "final_iteration_error": dare_error,
            "Pi": P_inf,
            "K_inf": K_inf,
            "closed_loop_eigenvalues": eig_inf,
            "spectral_radius": rho_inf,
            "stable_rho_lt_1": bool(rho_inf < 1.0),
        },
        "finite_horizon_records": [
            {
                "horizon": r.horizon,
                "K": r.K,
                "P": r.P,
                "closed_loop_eigenvalues": r.eig_closed_loop,
                "spectral_radius": r.spectral_radius,
                "stable_rho_lt_1": r.stable,
                "K_error_to_K_inf_fro": r.K_error_to_inf,
                "P_error_to_P_inf_fro": r.P_error_to_inf,
            }
            for r in records
        ],
        "lyapunov_check": {
            "case": "infinite_horizon",
            "max_abs_delta_plus_stage_residual": float(np.nanmax(np.abs(simulations["infinite_horizon"]["lyapunov_residual"]))),
            "V_monotone_nonincreasing": bool(np.all(np.diff(simulations["infinite_horizon"]["V"]) <= 1e-9)),
            "initial_state": x0,
            "final_state": simulations["infinite_horizon"]["X"][-1],
            "initial_state_norm": simulations["infinite_horizon"]["state_norm"][0],
            "final_state_norm": simulations["infinite_horizon"]["state_norm"][-1],
        },
        "plots": plot_paths,
    }

    write_json(out_dir / "lqr_convergence_results.json", result)
    write_report(
        out_dir / "lqr_convergence_report.md",
        system,
        controllability,
        P_inf,
        K_inf,
        dare_source,
        dare_iterations,
        dare_error,
        eig_inf,
        rho_inf,
        records,
        simulations,
        plot_paths,
    )

    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sandbox for Rawlings Section 1.3.6 LQR convergence."
    )
    parser.add_argument(
        "--out",
        default="out/convergence_lqr",
        help="Output directory. Default: out/convergence_lqr",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=40,
        help="Closed-loop simulation steps. Default: 40",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    out_dir = Path(args.out).expanduser().resolve()
    result = run(out_dir, steps=args.steps)

    print("LQR convergence sandbox complete.")
    print(f"Output directory: {result['output_directory']}")
    print(f"Controllable: {result['controllability']['controllable']}")
    print(f"Infinite-horizon spectral radius: {result['dare']['spectral_radius']:.10g}")
    print(f"Stable/convergent: {result['dare']['stable_rho_lt_1']}")
    print("Files:")
    for name in [
        "lqr_convergence_results.json",
        "riccati_iteration_log.csv",
        "closed_loop_trajectory.csv",
        "lqr_convergence_report.md",
    ]:
        print(f"  {out_dir / name}")
    for p in result.get("plots", {}).values():
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
