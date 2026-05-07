#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
convergence_state_estimator.py

Rawlings, Mayne, and Diehl Section 1.4.6 sandbox:
Convergence of the state estimator.

This script is intentionally standalone. It builds a transparent finite-
horizon least-squares / full-information estimator and checks the exact
ideas in Section 1.4.6:

1. The optimal estimator cost V_T^0 is nondecreasing and bounded above for
   noise-free measurements.
2. For an observable pair (A, C), the estimated current state converges to
   the true current state as more measurements become available.
3. For an unobservable pair, optimal estimation does not necessarily converge.
4. A recursive Kalman filter view gives the same engineering picture: the
   estimator error dynamics become stable when the system is observable or
   detectable and the weights are sensible.

Outputs are written to:
    out/convergence_state_estimator

Run:
    python convergence_state_estimator.py

or, if copied into the model_predictive_control package directory:
    python sandbox/convergence_state_estimator.py
"""

from dataclasses import dataclass
from pathlib import Path
import csv
import json
import math
from typing import Iterable

import numpy as np
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# Small numerical helpers
# ---------------------------------------------------------------------------


def as_list(a: np.ndarray) -> list:
    arr = np.asarray(a)
    if np.iscomplexobj(arr):
        return [{"real": float(np.real(v)), "imag": float(np.imag(v))} for v in arr.reshape(-1)] if arr.ndim == 1 else [[{"real": float(np.real(v)), "imag": float(np.imag(v))} for v in row] for row in arr]
    return arr.tolist()


def mat_str(a: np.ndarray, precision: int = 6) -> str:
    return np.array2string(np.asarray(a), precision=precision, suppress_small=False)


def spectral_radius(a: np.ndarray) -> float:
    eig = np.linalg.eigvals(a)
    return float(np.max(np.abs(eig)))


def matrix_sqrt_weight(w: np.ndarray) -> np.ndarray:
    """Return a square root of a symmetric positive definite weight matrix."""
    w = np.asarray(w, dtype=float)
    vals, vecs = np.linalg.eigh(w)
    if np.any(vals <= 0):
        raise ValueError(f"Weight matrix must be positive definite. eigenvalues={vals}")
    return vecs @ np.diag(np.sqrt(vals)) @ vecs.T


def block_set(m: np.ndarray, row: int, col: int, block: np.ndarray, n: int) -> None:
    r0 = row * n
    c0 = col * n
    m[r0:r0 + block.shape[0], c0:c0 + block.shape[1]] = block


def observability_matrix(A: np.ndarray, C: np.ndarray, blocks: int | None = None) -> np.ndarray:
    n = A.shape[0]
    blocks = n if blocks is None else blocks
    rows = []
    power = np.eye(n)
    for _ in range(blocks):
        rows.append(C @ power)
        power = power @ A
    return np.vstack(rows)


def hautus_ranks(A: np.ndarray, C: np.ndarray) -> list[dict[str, object]]:
    n = A.shape[0]
    out = []
    for lam in np.linalg.eigvals(A):
        H = np.vstack([lam * np.eye(n) - A, C])
        out.append({
            "lambda_real": float(np.real(lam)),
            "lambda_imag": float(np.imag(lam)),
            "rank": int(np.linalg.matrix_rank(H, tol=1e-9)),
            "required_rank": int(n),
        })
    return out


# ---------------------------------------------------------------------------
# Full information / batch least-squares estimator
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EstimatorCase:
    name: str
    A: np.ndarray
    C: np.ndarray
    Q: np.ndarray       # process-noise covariance used in penalty Q^{-1}
    R: np.ndarray       # measurement-noise covariance used in penalty R^{-1}
    P0: np.ndarray      # prior covariance used in penalty P0^{-1}
    x0_true: np.ndarray
    x0_prior: np.ndarray
    steps: int


def simulate_noise_free(A: np.ndarray, C: np.ndarray, x0: np.ndarray, steps: int) -> tuple[np.ndarray, np.ndarray]:
    """Return x(0:steps), y(0:steps) for x+ = A x, y = C x."""
    n = A.shape[0]
    p = C.shape[0]
    X = np.zeros((steps + 1, n))
    Y = np.zeros((steps + 1, p))
    X[0] = x0
    Y[0] = C @ X[0]
    for k in range(steps):
        X[k + 1] = A @ X[k]
        Y[k + 1] = C @ X[k + 1]
    return X, Y


def solve_full_information_ls(
    A: np.ndarray,
    C: np.ndarray,
    Q: np.ndarray,
    R: np.ndarray,
    P0: np.ndarray,
    x0_prior: np.ndarray,
    Y: np.ndarray,
    T: int,
) -> dict[str, object]:
    """Solve the unconstrained full-information quadratic estimator.

    Decision variable is z = [x(0), x(1), ..., x(T)].

    Minimize
        1/2 |x(0) - xbar(0)|^2_{P0^{-1}}
      + 1/2 sum_{k=0}^{T-1} |x(k+1) - A x(k)|^2_{Q^{-1}}
      + 1/2 sum_{k=0}^{T} |y(k) - C x(k)|^2_{R^{-1}}
    """
    n = A.shape[0]
    p = C.shape[0]
    rows = []
    rhs = []

    Sp = matrix_sqrt_weight(np.linalg.inv(P0))
    Sq = matrix_sqrt_weight(np.linalg.inv(Q))
    Sr = matrix_sqrt_weight(np.linalg.inv(R))

    # Prior residual: Sp x(0) = Sp xbar(0)
    H = np.zeros((n, (T + 1) * n))
    H[:, 0:n] = Sp
    rows.append(H)
    rhs.append(Sp @ x0_prior)

    # Process residuals: Sq x(k+1) - Sq A x(k) = 0
    for k in range(T):
        H = np.zeros((n, (T + 1) * n))
        H[:, k * n:(k + 1) * n] = -Sq @ A
        H[:, (k + 1) * n:(k + 2) * n] = Sq
        rows.append(H)
        rhs.append(np.zeros(n))

    # Measurement residuals: Sr C x(k) = Sr y(k)
    for k in range(T + 1):
        H = np.zeros((p, (T + 1) * n))
        H[:, k * n:(k + 1) * n] = Sr @ C
        rows.append(H)
        rhs.append(Sr @ Y[k])

    H_all = np.vstack(rows)
    b_all = np.concatenate(rhs)
    z, residuals, rank, singular_values = np.linalg.lstsq(H_all, b_all, rcond=None)
    residual_vec = H_all @ z - b_all
    cost = 0.5 * float(residual_vec.T @ residual_vec)
    Xhat = z.reshape(T + 1, n)

    return {
        "T": T,
        "Xhat": Xhat,
        "cost": cost,
        "rank": int(rank),
        "normal_matrix_condition": float(np.linalg.cond(H_all.T @ H_all)),
        "singular_values_min": float(np.min(singular_values)),
        "singular_values_max": float(np.max(singular_values)),
    }


def run_batch_convergence(case: EstimatorCase) -> dict[str, object]:
    A, C, Q, R, P0 = case.A, case.C, case.Q, case.R, case.P0
    Xtrue, Y = simulate_noise_free(A, C, case.x0_true, case.steps)
    n = A.shape[0]

    filtered_rows = []
    smoothed_rows = []
    costs = []
    batch_solutions: dict[int, dict[str, object]] = {}

    for T in range(case.steps + 1):
        sol = solve_full_information_ls(A, C, Q, R, P0, case.x0_prior, Y, T)
        batch_solutions[T] = sol
        xhat_T_T = np.asarray(sol["Xhat"])[T]
        err = Xtrue[T] - xhat_T_T
        costs.append(float(sol["cost"]))
        filtered_rows.append({
            "k": T,
            "cost": float(sol["cost"]),
            "x1_true": Xtrue[T, 0],
            "x2_true": Xtrue[T, 1] if n > 1 else math.nan,
            "x1_hat_filtered": xhat_T_T[0],
            "x2_hat_filtered": xhat_T_T[1] if n > 1 else math.nan,
            "filtered_error_norm": float(np.linalg.norm(err)),
            "normal_matrix_condition": float(sol["normal_matrix_condition"]),
        })

    # Smoothed estimate used in the proof idea: xhat(k | k+n-1), when available.
    for k in range(case.steps - n + 2):
        Tend = k + n - 1
        sol = batch_solutions[Tend]
        xhat_k_future = np.asarray(sol["Xhat"])[k]
        err = Xtrue[k] - xhat_k_future
        smoothed_rows.append({
            "k": k,
            "T_used": Tend,
            "x1_true": Xtrue[k, 0],
            "x2_true": Xtrue[k, 1] if n > 1 else math.nan,
            "x1_hat_smoothed": xhat_k_future[0],
            "x2_hat_smoothed": xhat_k_future[1] if n > 1 else math.nan,
            "smoothed_error_norm": float(np.linalg.norm(err)),
        })

    diffs = np.diff(np.asarray(costs))
    return {
        "Xtrue": Xtrue,
        "Y": Y,
        "filtered_rows": filtered_rows,
        "smoothed_rows": smoothed_rows,
        "costs": costs,
        "cost_non_decreasing_check": bool(np.all(diffs >= -1e-9)),
        "largest_negative_cost_step": float(np.min(diffs)) if diffs.size else 0.0,
        "final_filtered_error_norm": filtered_rows[-1]["filtered_error_norm"],
        "final_smoothed_error_norm": smoothed_rows[-1]["smoothed_error_norm"] if smoothed_rows else None,
    }


# ---------------------------------------------------------------------------
# Recursive Kalman filter comparison
# ---------------------------------------------------------------------------


def run_recursive_kalman(case: EstimatorCase) -> dict[str, object]:
    A, C, Q, R = case.A, case.C, case.Q, case.R
    Xtrue, Y = simulate_noise_free(A, C, case.x0_true, case.steps)
    n = A.shape[0]
    xhat = case.x0_prior.copy()
    P = case.P0.copy()
    I = np.eye(n)
    rows = []
    gains = []
    eig_error = []

    # Measurement update at k=0, then predict/update for k>=1.
    for k in range(case.steps + 1):
        if k > 0:
            xhat = A @ xhat
            P = A @ P @ A.T + Q

        innovation = Y[k] - C @ xhat
        S = C @ P @ C.T + R
        K = P @ C.T @ np.linalg.inv(S)
        xhat = xhat + K @ innovation
        P = (I - K @ C) @ P @ (I - K @ C).T + K @ R @ K.T  # Joseph form
        err = Xtrue[k] - xhat
        gains.append(K.copy())
        transition = (I - K @ C) @ A
        eig_error.append(np.linalg.eigvals(transition))
        rows.append({
            "k": k,
            "x1_true": Xtrue[k, 0],
            "x2_true": Xtrue[k, 1] if n > 1 else math.nan,
            "x1_hat_kalman": xhat[0],
            "x2_hat_kalman": xhat[1] if n > 1 else math.nan,
            "kalman_error_norm": float(np.linalg.norm(err)),
            "gain_1": K[0, 0] if K.size else math.nan,
            "gain_2": K[1, 0] if K.shape[0] > 1 and K.shape[1] > 0 else math.nan,
            "error_transition_spectral_radius": spectral_radius(transition),
        })

    return {
        "rows": rows,
        "final_gain": gains[-1],
        "final_error_transition_eigs": eig_error[-1],
        "final_error_transition_spectral_radius": float(rows[-1]["error_transition_spectral_radius"]),
        "final_error_norm": float(rows[-1]["kalman_error_norm"]),
    }


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    keys = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def write_log(path: Path, lines: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for line in lines:
            f.write(line.rstrip() + "\n")


def plot_case(out_dir: Path, case: EstimatorCase, batch: dict[str, object], kalman: dict[str, object]) -> list[Path]:
    paths = []
    filtered = batch["filtered_rows"]
    smoothed = batch["smoothed_rows"]
    kal_rows = kalman["rows"]
    k = np.array([r["k"] for r in filtered], dtype=float)
    cost = np.array(batch["costs"], dtype=float)
    filt_err = np.array([r["filtered_error_norm"] for r in filtered], dtype=float)
    kal_err = np.array([r["kalman_error_norm"] for r in kal_rows], dtype=float)

    if smoothed:
        ks = np.array([r["k"] for r in smoothed], dtype=float)
        smooth_err = np.array([r["smoothed_error_norm"] for r in smoothed], dtype=float)
    else:
        ks = np.array([])
        smooth_err = np.array([])

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(k, cost, marker="o", markersize=3)
    ax.set_title(f"{case.name}: optimal estimator cost V_T^0")
    ax.set_xlabel("T")
    ax.set_ylabel("optimal cost")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    p = out_dir / f"{case.name}_cost_convergence.png"
    fig.savefig(p, dpi=160)
    paths.append(p)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.semilogy(k, filt_err + 1e-15, label="FIE filtered error ||x(k)-xhat(k|k)||")
    if smooth_err.size:
        ax.semilogy(ks, smooth_err + 1e-15, label="FIE smoothed error ||x(k)-xhat(k|k+n-1)||")
    ax.semilogy(k, kal_err + 1e-15, label="recursive Kalman error")
    ax.set_title(f"{case.name}: state-estimate error convergence")
    ax.set_xlabel("k")
    ax.set_ylabel("error norm, log scale")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    p = out_dir / f"{case.name}_error_convergence.png"
    fig.savefig(p, dpi=160)
    paths.append(p)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    Xtrue = np.asarray(batch["Xtrue"])
    x1hat = np.array([r["x1_hat_filtered"] for r in filtered], dtype=float)
    ax.plot(k, Xtrue[:, 0], label="true x1")
    ax.plot(k, x1hat, linestyle="--", label="FIE filtered xhat1")
    if Xtrue.shape[1] > 1:
        x2hat = np.array([r["x2_hat_filtered"] for r in filtered], dtype=float)
        ax.plot(k, Xtrue[:, 1], label="true x2")
        ax.plot(k, x2hat, linestyle="--", label="FIE filtered xhat2")
    ax.set_title(f"{case.name}: true state versus batch estimate")
    ax.set_xlabel("k")
    ax.set_ylabel("state value")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    p = out_dir / f"{case.name}_states_vs_estimates.png"
    fig.savefig(p, dpi=160)
    paths.append(p)
    plt.close(fig)

    return paths


def make_case_logs(case: EstimatorCase, batch: dict[str, object], kalman: dict[str, object]) -> list[str]:
    A, C, Q, R, P0 = case.A, case.C, case.Q, case.R, case.P0
    O = observability_matrix(A, C)
    O_rank = np.linalg.matrix_rank(O, tol=1e-9)
    h_ranks = hautus_ranks(A, C)
    costs = np.asarray(batch["costs"], dtype=float)
    prior_bound = 0.5 * float((case.x0_true - case.x0_prior).T @ np.linalg.inv(P0) @ (case.x0_true - case.x0_prior))
    rows = batch["filtered_rows"]
    kal_rows = kalman["rows"]

    lines = []
    lines.append("Convergence of the State Estimator - Calculation Log")
    lines.append("Rawlings / Mayne / Diehl Section 1.4.6 sandbox")
    lines.append("")
    lines.append(f"Case: {case.name}")
    lines.append("")
    lines.append("Model used")
    lines.append("  x(k+1) = A x(k) + w(k)")
    lines.append("  y(k)   = C x(k) + v(k)")
    lines.append("  For the convergence check, the generated data are noise-free:")
    lines.append("  w(k)=0 and v(k)=0, so y(k)=C A^k x(0).")
    lines.append("")
    lines.append("Matrices")
    lines.append(f"  A =\n{mat_str(A)}")
    lines.append(f"  C =\n{mat_str(C)}")
    lines.append(f"  Q covariance =\n{mat_str(Q)}")
    lines.append(f"  R covariance =\n{mat_str(R)}")
    lines.append(f"  P0 prior covariance =\n{mat_str(P0)}")
    lines.append(f"  true x(0)  = {mat_str(case.x0_true)}")
    lines.append(f"  prior xbar(0) = {mat_str(case.x0_prior)}")
    lines.append("")
    lines.append("Observability checks")
    lines.append(f"  O = [C; C A; ...; C A^(n-1)] =\n{mat_str(O)}")
    lines.append(f"  rank(O) = {O_rank}, required rank = {A.shape[0]}")
    for item in h_ranks:
        lines.append(
            "  Hautus at lambda = "
            f"{item['lambda_real']:.8g} + {item['lambda_imag']:.8g}j: "
            f"rank([lambda I - A; C]) = {item['rank']} / {item['required_rank']}"
        )
    lines.append("")
    lines.append("Full-information / batch least-squares objective")
    lines.append("  Decision vector z = [x(0), x(1), ..., x(T)].")
    lines.append("  Minimize:")
    lines.append("    1/2 |x(0)-xbar(0)|^2_{P0^{-1}}")
    lines.append("  + 1/2 sum |x(k+1)-A x(k)|^2_{Q^{-1}}")
    lines.append("  + 1/2 sum |y(k)-C x(k)|^2_{R^{-1}}")
    lines.append("")
    lines.append("Lemma 1.5 numerical check")
    lines.append(f"  V_T^0 nondecreasing? {batch['cost_non_decreasing_check']}")
    lines.append(f"  largest negative cost increment = {batch['largest_negative_cost_step']:.12e}")
    lines.append(f"  upper-bound candidate using true trajectory = {prior_bound:.12g}")
    lines.append(f"  final V_T^0 = {costs[-1]:.12g}")
    lines.append("  First six costs:")
    for i, v in enumerate(costs[:6]):
        lines.append(f"    T={i:2d}: V_T^0 = {v:.12g}")
    lines.append("  Last six costs:")
    for i in range(max(0, len(costs) - 6), len(costs)):
        lines.append(f"    T={i:2d}: V_T^0 = {costs[i]:.12g}")
    lines.append("")
    lines.append("Lemma 1.6 numerical check")
    lines.append("  Main observable-case statement: xhat(T|T) -> x(T).")
    lines.append(f"  initial filtered error norm = {rows[0]['filtered_error_norm']:.12g}")
    lines.append(f"  final filtered error norm   = {rows[-1]['filtered_error_norm']:.12g}")
    if batch["final_smoothed_error_norm"] is not None:
        lines.append(f"  final smoothed error norm   = {batch['final_smoothed_error_norm']:.12g}")
    lines.append("")
    lines.append("Selected filtered-estimator calculations")
    for r in rows[:4] + rows[-4:]:
        lines.append(
            f"  k={int(r['k']):2d}: true=({r['x1_true']:.8g}, {r['x2_true']:.8g}), "
            f"xhat=({r['x1_hat_filtered']:.8g}, {r['x2_hat_filtered']:.8g}), "
            f"||error||={r['filtered_error_norm']:.8g}, V={r['cost']:.8g}"
        )
    lines.append("")
    lines.append("Recursive Kalman filter comparison")
    lines.append(f"  final Kalman gain L/K =\n{mat_str(np.asarray(kalman['final_gain']))}")
    lines.append(f"  final error-transition eigenvalues eig((I-LC)A) = {mat_str(np.asarray(kalman['final_error_transition_eigs']))}")
    lines.append(f"  final error-transition spectral radius = {kalman['final_error_transition_spectral_radius']:.12g}")
    lines.append(f"  final recursive Kalman error norm = {kalman['final_error_norm']:.12g}")
    lines.append("  First and last recursive rows:")
    for r in kal_rows[:3] + kal_rows[-3:]:
        lines.append(
            f"    k={int(r['k']):2d}: K=({r['gain_1']:.8g}, {r['gain_2']:.8g}), "
            f"rho={r['error_transition_spectral_radius']:.8g}, "
            f"||error||={r['kalman_error_norm']:.8g}"
        )
    lines.append("")
    lines.append("Engineering interpretation")
    if O_rank == A.shape[0]:
        lines.append("  This pair (A, C) is observable. The measurements contain enough")
        lines.append("  information to reconstruct the hidden state. The optimizer can start")
        lines.append("  from a bad prior and still drive the estimate error toward zero as")
        lines.append("  more measurements are used.")
    else:
        lines.append("  This pair (A, C) is not observable. The measurements do not contain")
        lines.append("  enough information to reconstruct the hidden state. Optimality alone")
        lines.append("  is not a stability guarantee; the estimate can remain wrong.")
    return lines


def main() -> int:
    out_dir = Path("out/convergence_state_estimator").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    observable = EstimatorCase(
        name="observable_double_integrator",
        A=np.array([[1.0, 1.0], [0.0, 1.0]]),
        C=np.array([[1.0, 0.0]]),
        Q=np.diag([0.08, 0.08]),
        R=np.array([[0.35]]),
        P0=np.diag([8.0, 8.0]),
        x0_true=np.array([1.5, 0.25]),
        x0_prior=np.array([8.0, -4.0]),
        steps=40,
    )

    unobservable = EstimatorCase(
        name="unobservable_identity_no_measurement",
        A=np.eye(2),
        C=np.array([[0.0, 0.0]]),
        Q=np.diag([0.08, 0.08]),
        R=np.array([[0.35]]),
        P0=np.diag([8.0, 8.0]),
        x0_true=np.array([1.5, 0.25]),
        x0_prior=np.array([8.0, -4.0]),
        steps=40,
    )

    all_summary = {}
    generated_files: list[str] = []

    for case in [observable, unobservable]:
        batch = run_batch_convergence(case)
        kalman = run_recursive_kalman(case)

        filtered_csv = out_dir / f"{case.name}_batch_filtered.csv"
        smoothed_csv = out_dir / f"{case.name}_batch_smoothed.csv"
        kalman_csv = out_dir / f"{case.name}_kalman.csv"
        log_path = out_dir / f"{case.name}_calculation_log.txt"

        write_csv(filtered_csv, batch["filtered_rows"])
        write_csv(smoothed_csv, batch["smoothed_rows"])
        write_csv(kalman_csv, kalman["rows"])
        write_log(log_path, make_case_logs(case, batch, kalman))
        plots = plot_case(out_dir, case, batch, kalman)

        generated_files.extend([str(filtered_csv), str(smoothed_csv), str(kalman_csv), str(log_path)])
        generated_files.extend(str(p) for p in plots)

        O = observability_matrix(case.A, case.C)
        all_summary[case.name] = {
            "A": as_list(case.A),
            "C": as_list(case.C),
            "observability_matrix": as_list(O),
            "observability_rank": int(np.linalg.matrix_rank(O, tol=1e-9)),
            "required_rank": int(case.A.shape[0]),
            "hautus_ranks": hautus_ranks(case.A, case.C),
            "cost_non_decreasing_check": batch["cost_non_decreasing_check"],
            "initial_filtered_error_norm": batch["filtered_rows"][0]["filtered_error_norm"],
            "final_filtered_error_norm": batch["final_filtered_error_norm"],
            "final_smoothed_error_norm": batch["final_smoothed_error_norm"],
            "final_kalman_error_norm": kalman["final_error_norm"],
            "final_kalman_gain": as_list(kalman["final_gain"]),
            "final_error_transition_eigs": as_list(np.asarray(kalman["final_error_transition_eigs"])),
            "final_error_transition_spectral_radius": kalman["final_error_transition_spectral_radius"],
        }

    summary_path = out_dir / "convergence_state_estimator_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(all_summary, f, indent=2)
        f.write("\n")
    generated_files.append(str(summary_path))

    readme_path = out_dir / "README.txt"
    write_log(readme_path, [
        "Convergence State Estimator Sandbox Outputs",
        "============================================",
        "",
        "The script created two cases:",
        "  1. observable_double_integrator",
        "  2. unobservable_identity_no_measurement",
        "",
        "For each case, inspect:",
        "  *_calculation_log.txt       actual matrix/rank/cost/gain calculations",
        "  *_batch_filtered.csv        full-information estimate xhat(k|k)",
        "  *_batch_smoothed.csv        smoothed estimate xhat(k|k+n-1)",
        "  *_kalman.csv                recursive Kalman estimate and gain history",
        "  *_cost_convergence.png      V_T^0 versus T",
        "  *_error_convergence.png     estimate-error norm versus k",
        "  *_states_vs_estimates.png   true states versus batch estimates",
        "",
        "Main lesson:",
        "  The observable case converges. The unobservable case demonstrates why",
        "  Rawlings/Mayne/Diehl warn that optimality alone does not ensure estimator",
        "  stability.",
    ])
    generated_files.append(str(readme_path))

    print("Convergence state estimator sandbox complete.")
    print(f"Output directory: {out_dir}")
    print("Generated files:")
    for path in generated_files:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
