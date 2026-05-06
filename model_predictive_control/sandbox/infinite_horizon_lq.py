#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
section_1_3_4_infinite_horizon_lq_sandbox.py

Sandbox for Rawlings, Mayne, and Diehl, MPC: Theory, Computation,
and Design, Section 1.3.4, "The Infinite Horizon LQ Problem".

Purpose
-------
This script reproduces the textbook's finite-horizon Riccati iteration
example on pages 21-22 and then pushes it to the infinite-horizon / steady
state limit.

The textbook's point is subtle and important:

    A finite-horizon LQ controller can be optimal over its finite prediction
    window and still destabilize the closed-loop system when reused forever
    as a fixed feedback gain.

The script calculates:

1. The finite-horizon first feedback gain K(0) for several horizons N.
2. The closed-loop eigenvalues of A + B K(0).
3. The discrete-time stability margin, defined here as 1 - rho(A + B K),
   where rho is the spectral radius. Positive margin means all eigenvalues
   are inside the unit circle.
4. The steady-state DARE solution and the infinite-horizon gain.
5. Plots and CSV/JSON files for studying convergence.

Run
---
From any folder:

    python section_1_3_4_infinite_horizon_lq_sandbox.py

Optional:

    python section_1_3_4_infinite_horizon_lq_sandbox.py --max-horizon 80 --show

Outputs
-------
By default, outputs are written to:

    ./out/section_1_3_4_infinite_horizon_lq/

Files include:

    riccati_horizon_sweep.csv
    summary.json
    spectral_radius_vs_horizon.png
    eigenvalue_map.png
    riccati_convergence.png
    closed_loop_state_comparison.png
"""

from dataclasses import asdict, dataclass
from pathlib import Path
import argparse
import csv
import json
import math
from typing import Iterable

import numpy as np

try:
    import matplotlib.pyplot as plt
except Exception as exc:  # pragma: no cover
    raise SystemExit("matplotlib is required for this sandbox script") from exc

try:
    from scipy.linalg import solve_discrete_are
except Exception:  # pragma: no cover
    solve_discrete_are = None


Array = np.ndarray


@dataclass
class HorizonResult:
    horizon: int
    K: list[float]
    P0: list[list[float]]
    eig_real_1: float
    eig_imag_1: float
    eig_abs_1: float
    eig_real_2: float
    eig_imag_2: float
    eig_abs_2: float
    spectral_radius: float
    discrete_stability_margin: float
    stable: bool
    P0_minus_Pinf_fro: float | None = None


def rawlings_section_1_3_4_data() -> tuple[Array, Array, Array, Array, Array]:
    """Return A, B, C, Q, R from the Section 1.3.4 example."""

    A = np.array([[4.0 / 3.0, -2.0 / 3.0], [1.0, 0.0]], dtype=float)
    B = np.array([[1.0], [0.0]], dtype=float)
    C = np.array([[-2.0 / 3.0, 1.0]], dtype=float)
    Q = C.T @ C + 0.001 * np.eye(2)
    R = np.array([[0.001]], dtype=float)
    return A, B, C, Q, R


def riccati_backward(A: Array, B: Array, Q: Array, R: Array, Pf: Array, N: int) -> tuple[list[Array], list[Array]]:
    """Run the backward Riccati recursion from P(N)=Pf to P(0).

    Returns
    -------
    P_seq:
        List of P(k), k=0..N.
    K_seq:
        List of K(k), k=0..N-1, where u(k) = K(k) x(k).
    """

    if N < 1:
        raise ValueError("N must be at least 1")

    P_seq = [np.zeros_like(Q) for _ in range(N + 1)]
    K_seq = [np.zeros((B.shape[1], A.shape[0])) for _ in range(N)]
    P_seq[N] = Pf.copy()

    for k in range(N - 1, -1, -1):
        P_next = P_seq[k + 1]
        S = B.T @ P_next @ B + R
        K = -np.linalg.solve(S, B.T @ P_next @ A)
        P = Q + A.T @ P_next @ A - A.T @ P_next @ B @ np.linalg.solve(S, B.T @ P_next @ A)
        K_seq[k] = K
        P_seq[k] = 0.5 * (P + P.T)  # keep numerical symmetry

    return P_seq, K_seq


def finite_horizon_first_gain(A: Array, B: Array, Q: Array, R: Array, Pf: Array, N: int) -> tuple[Array, Array]:
    """Return P(0), K(0) for horizon N."""

    P_seq, K_seq = riccati_backward(A, B, Q, R, Pf, N)
    return P_seq[0], K_seq[0]


def dare_fixed_point_iteration(A: Array, B: Array, Q: Array, R: Array, P0: Array, max_iter: int = 10_000, tol: float = 1e-13) -> tuple[Array, Array, int, float]:
    """Approximate the infinite-horizon DARE solution by repeated Riccati updates.

    This mirrors the book's logic: keep increasing the horizon, and the first
    gain K(0) approaches a steady-state gain.
    """

    P = P0.copy()
    last_err = math.inf
    for i in range(1, max_iter + 1):
        S = B.T @ P @ B + R
        P_new = Q + A.T @ P @ A - A.T @ P @ B @ np.linalg.solve(S, B.T @ P @ A)
        P_new = 0.5 * (P_new + P_new.T)
        last_err = float(np.linalg.norm(P_new - P, ord="fro"))
        P = P_new
        if last_err < tol:
            break

    K = -np.linalg.solve(B.T @ P @ B + R, B.T @ P @ A)
    return P, K, i, last_err


def closed_loop_metrics(A: Array, B: Array, K: Array) -> tuple[Array, float, float, bool]:
    """Return eigenvalues, spectral radius, unit-circle margin, stability flag."""

    Acl = A + B @ K
    eigvals = np.linalg.eigvals(Acl)
    rho = float(np.max(np.abs(eigvals)))
    margin = 1.0 - rho
    stable = bool(rho < 1.0)
    return eigvals, rho, margin, stable


def sort_eigs_for_display(eigvals: Iterable[complex]) -> list[complex]:
    """Sort eigenvalues by descending magnitude for repeatable CSV/JSON output."""

    return sorted([complex(v) for v in eigvals], key=lambda z: (-abs(z), z.real, z.imag))


def simulate_closed_loop(A: Array, B: Array, K: Array, x0: Array, steps: int) -> Array:
    """Simulate x(k+1) = (A + B K) x(k)."""

    X = np.zeros((steps + 1, A.shape[0]))
    X[0] = x0
    Acl = A + B @ K
    for k in range(steps):
        X[k + 1] = Acl @ X[k]
    return X


def to_jsonable(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag, "abs": abs(value)}
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    return value


def write_csv(path: Path, rows: list[HorizonResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(rows[0]).keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def make_plots(out_dir: Path, rows: list[HorizonResult], A: Array, B: Array, K_inf: Array, P_inf: Array, show: bool) -> None:
    horizons = np.array([r.horizon for r in rows], dtype=float)
    rho = np.array([r.spectral_radius for r in rows], dtype=float)
    margin = np.array([r.discrete_stability_margin for r in rows], dtype=float)
    p_err = np.array([np.nan if r.P0_minus_Pinf_fro is None else r.P0_minus_Pinf_fro for r in rows], dtype=float)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(horizons, rho, marker="o", linewidth=1.5, markersize=3)
    ax.axhline(1.0, linestyle="--", linewidth=1.0, label="unit-circle boundary")
    ax.set_title("Closed-loop spectral radius vs finite LQ horizon")
    ax.set_xlabel("finite horizon N")
    ax.set_ylabel("rho(A + B K(0))")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(out_dir / "spectral_radius_vs_horizon.png", dpi=170)
    if show:
        plt.show()
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.8, 6.8))
    theta = np.linspace(0.0, 2.0 * np.pi, 400)
    ax.plot(np.cos(theta), np.sin(theta), linestyle="--", linewidth=1.0, label="unit circle")
    for N in [5, 7, 10, 20, int(horizons[-1])]:
        if N < horizons[0] or N > horizons[-1]:
            continue
        row = next(r for r in rows if r.horizon == N)
        eigs = [complex(row.eig_real_1, row.eig_imag_1), complex(row.eig_real_2, row.eig_imag_2)]
        ax.scatter([z.real for z in eigs], [z.imag for z in eigs], label=f"N={N}")
    eig_inf, _, _, _ = closed_loop_metrics(A, B, K_inf)
    ax.scatter([z.real for z in eig_inf], [z.imag for z in eig_inf], marker="x", s=80, label="steady state")
    ax.set_title("Closed-loop eigenvalues in the z-plane")
    ax.set_xlabel("real")
    ax.set_ylabel("imaginary")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(out_dir / "eigenvalue_map.png", dpi=170)
    if show:
        plt.show()
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.semilogy(horizons, p_err, marker="o", linewidth=1.5, markersize=3)
    ax.set_title("Riccati matrix convergence toward steady-state DARE solution")
    ax.set_xlabel("finite horizon N")
    ax.set_ylabel("||P_N(0) - P_infinity||_F")
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "riccati_convergence.png", dpi=170)
    if show:
        plt.show()
    plt.close(fig)

    x0 = np.array([1.0, 0.0])
    steps = 35
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for label, K in [
        ("N=5 unstable finite-horizon gain", np.array(rows[4].K).reshape(1, 2) if len(rows) >= 5 else K_inf),
        ("N=7 stabilizing finite-horizon gain", np.array(rows[6].K).reshape(1, 2) if len(rows) >= 7 else K_inf),
        ("steady-state gain", K_inf),
    ]:
        X = simulate_closed_loop(A, B, K, x0, steps)
        norms = np.linalg.norm(X, axis=1)
        ax.plot(np.arange(steps + 1), norms, marker="o", markersize=2.5, linewidth=1.5, label=label)
    ax.set_title("Closed-loop state norm from x0 = [1, 0]")
    ax.set_xlabel("sample k")
    ax.set_ylabel("||x(k)||_2")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(out_dir / "closed_loop_state_comparison.png", dpi=170)
    if show:
        plt.show()
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description="Rawlings Section 1.3.4 infinite-horizon LQ sandbox")
    parser.add_argument("--max-horizon", type=int, default=60, help="largest finite horizon N to sweep")
    parser.add_argument("--out", type=str, default="out/infinite_horizon_lq", help="output directory")
    parser.add_argument("--show", action="store_true", help="show Matplotlib figures interactively")
    args = parser.parse_args()

    if args.max_horizon < 7:
        raise SystemExit("--max-horizon must be at least 7 so the N=5 and N=7 textbook checks are included")

    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    A, B, C, Q, R = rawlings_section_1_3_4_data()
    Pf = Q.copy()

    P_iter, K_iter, dare_iters, dare_err = dare_fixed_point_iteration(A, B, Q, R, Pf)

    if solve_discrete_are is not None:
        P_scipy = solve_discrete_are(A, B, Q, R)
        K_scipy = -np.linalg.solve(B.T @ P_scipy @ B + R, B.T @ P_scipy @ A)
        P_inf = 0.5 * (P_scipy + P_scipy.T)
        K_inf = K_scipy
        dare_source = "scipy.linalg.solve_discrete_are"
        dare_crosscheck_fro = float(np.linalg.norm(P_iter - P_scipy, ord="fro"))
    else:
        P_inf = P_iter
        K_inf = K_iter
        dare_source = "fixed-point Riccati iteration only; scipy.linalg.solve_discrete_are unavailable"
        dare_crosscheck_fro = None

    eig_inf, rho_inf, margin_inf, stable_inf = closed_loop_metrics(A, B, K_inf)

    rows: list[HorizonResult] = []
    for N in range(1, args.max_horizon + 1):
        P0, K0 = finite_horizon_first_gain(A, B, Q, R, Pf, N)
        eigs, rho, margin, stable = closed_loop_metrics(A, B, K0)
        eigs_sorted = sort_eigs_for_display(eigs)
        rows.append(
            HorizonResult(
                horizon=N,
                K=[float(v) for v in K0.reshape(-1)],
                P0=P0.tolist(),
                eig_real_1=float(eigs_sorted[0].real),
                eig_imag_1=float(eigs_sorted[0].imag),
                eig_abs_1=float(abs(eigs_sorted[0])),
                eig_real_2=float(eigs_sorted[1].real),
                eig_imag_2=float(eigs_sorted[1].imag),
                eig_abs_2=float(abs(eigs_sorted[1])),
                spectral_radius=float(rho),
                discrete_stability_margin=float(margin),
                stable=stable,
                P0_minus_Pinf_fro=float(np.linalg.norm(P0 - P_inf, ord="fro")),
            )
        )

    write_csv(out_dir / "riccati_horizon_sweep.csv", rows)
    make_plots(out_dir, rows, A, B, K_inf, P_inf, args.show)

    textbook_focus = {N: asdict(rows[N - 1]) for N in [5, 7]}
    summary = {
        "title": "Rawlings Section 1.3.4 Infinite Horizon LQ Problem Sandbox",
        "source_note": "Uses the A, B, C, Q, R matrices shown in Rawlings/Mayne/Diehl, Section 1.3.4, pages 21-22.",
        "A": A,
        "B": B,
        "C": C,
        "Q": Q,
        "R": R,
        "Pf": Pf,
        "finite_horizon_textbook_focus": textbook_focus,
        "infinite_horizon": {
            "P_inf": P_inf,
            "K_inf": K_inf,
            "closed_loop_eigenvalues": sort_eigs_for_display(eig_inf),
            "spectral_radius": rho_inf,
            "discrete_stability_margin": margin_inf,
            "stable": stable_inf,
            "dare_source": dare_source,
            "fixed_point_iterations": dare_iters,
            "fixed_point_last_error": dare_err,
            "fixed_point_vs_scipy_fro_norm": dare_crosscheck_fro,
        },
        "interpretation": {
            "positive_discrete_stability_margin": "rho(A + B K) < 1, all closed-loop eigenvalues are inside the unit circle.",
            "negative_discrete_stability_margin": "rho(A + B K) > 1, at least one closed-loop eigenvalue is outside the unit circle.",
            "section_1_3_4_lesson": "Finite-horizon optimality alone does not guarantee stability if the first finite-horizon gain is reused forever. Increasing the horizon drives the Riccati recursion toward the stabilizing infinite-horizon gain.",
        },
        "output_files": {
            "csv": str(out_dir / "riccati_horizon_sweep.csv"),
            "spectral_radius_plot": str(out_dir / "spectral_radius_vs_horizon.png"),
            "eigenvalue_map": str(out_dir / "eigenvalue_map.png"),
            "riccati_convergence_plot": str(out_dir / "riccati_convergence.png"),
            "closed_loop_state_plot": str(out_dir / "closed_loop_state_comparison.png"),
        },
    }

    with (out_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(to_jsonable(summary), f, indent=2)
        f.write("\n")

    print("\nRawlings Section 1.3.4 Infinite-Horizon LQ Sandbox")
    print("=" * 62)
    print("A =\n", A)
    print("B =\n", B)
    print("C =\n", C)
    print("Q =\n", Q)
    print("R =\n", R)
    print("\nFinite-horizon checks")
    for N in [5, 7]:
        r = rows[N - 1]
        print(
            f"  N={N:2d}: K(0)={np.array(r.K)}, "
            f"eig={[(r.eig_real_1, r.eig_imag_1), (r.eig_real_2, r.eig_imag_2)]}, "
            f"rho={r.spectral_radius:.6f}, margin={r.discrete_stability_margin:.6f}, stable={r.stable}"
        )
    print("\nInfinite-horizon / steady-state check")
    print("  K_inf =", K_inf.reshape(-1))
    print("  eig(A + B K_inf) =", sort_eigs_for_display(eig_inf))
    print(f"  rho = {rho_inf:.6f}")
    print(f"  discrete stability margin = 1 - rho = {margin_inf:.6f}")
    print(f"  stable = {stable_inf}")
    print("\nFiles written to:")
    print(" ", out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
