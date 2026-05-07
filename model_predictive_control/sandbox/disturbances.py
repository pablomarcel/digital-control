#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
disturbances.py

Rawlings / Mayne / Diehl, Model Predictive Control, Section 1.5.2 sandbox:
Disturbances and zero offset.

This is a standalone learning script. It creates calculation logs, CSV files,
JSON summaries, and plots under out/disturbances.

Core idea:
  - A constant unknown disturbance can create steady-state tracking offset.
  - Add an integrating disturbance model d+ = d.
  - Estimate both x and d with an augmented estimator.
  - Re-solve the steady-state target problem with the current d_hat.
  - Regulate x_hat - x_s(d_hat) to zero.

Run:
  python disturbances.py

Outputs:
  out/disturbances/disturbances_calculation_log.txt
  out/disturbances/disturbances_summary.json
  out/disturbances/*_trajectory.csv
  out/disturbances/*_*.png
"""

from dataclasses import dataclass
from pathlib import Path
import csv
import json
import math
from typing import Any

import numpy as np
from numpy.linalg import matrix_rank, norm, eigvals
from scipy.linalg import solve_discrete_are


Array = np.ndarray


@dataclass
class DisturbanceCase:
    name: str
    description: str
    A: Array
    B: Array
    C: Array
    Bd: Array
    Cd: Array
    H: Array
    ysp: Array
    rsp: Array
    usp: Array
    d_true_final: Array
    step_time: int
    x0: Array
    xhat0: Array
    dhat0: Array
    Q_lqr: Array
    R_lqr: Array
    Qs: Array
    Rs: Array
    Qe: Array
    Re: Array
    steps: int = 70


def arr(x: Any) -> Array:
    return np.asarray(x, dtype=float)


def fmt_vec(v: Array, precision: int = 8) -> str:
    return np.array2string(np.asarray(v, dtype=float).reshape(-1), precision=precision, suppress_small=False)


def fmt_mat(M: Array, precision: int = 8) -> str:
    return np.array2string(np.asarray(M, dtype=float), precision=precision, suppress_small=False)


def spectral_radius(M: Array) -> float:
    return float(np.max(np.abs(eigvals(M))))


def lqr_gain(A: Array, B: Array, Q: Array, R: Array) -> tuple[Array, Array, Array, Array, float]:
    """Return P, K, Acl, eigenvalues, spectral radius for u = K x."""
    P = solve_discrete_are(A, B, Q, R)
    K = -np.linalg.solve(B.T @ P @ B + R, B.T @ P @ A)
    Acl = A + B @ K
    eig = eigvals(Acl)
    rho = spectral_radius(Acl)
    return P, K, Acl, eig, rho


def augmented_estimator_gain(A: Array, B: Array, C: Array, Bd: Array, Cd: Array, Qe: Array, Re: Array) -> tuple[Array, Array, Array, Array, Array, float]:
    """Steady-state Kalman-style gain for augmented state [x; d]."""
    n = A.shape[0]
    nd = Bd.shape[1]
    Az = np.block([
        [A, Bd],
        [np.zeros((nd, n)), np.eye(nd)],
    ])
    Bz = np.vstack([B, np.zeros((nd, B.shape[1]))])
    Cz = np.hstack([C, Cd])

    P = solve_discrete_are(Az.T, Cz.T, Qe, Re)
    L = P @ Cz.T @ np.linalg.inv(Cz @ P @ Cz.T + Re)
    Aerr = (np.eye(n + nd) - L @ Cz) @ Az
    return Az, Bz, Cz, P, L, spectral_radius(Aerr)


def target_selector(case: DisturbanceCase, dhat: Array) -> dict[str, Any]:
    """Solve the Section 1.5.2 disturbance-aware steady target problem.

    Variables are z = [xs; us].

    Constraints used here, ignoring inequality constraints:
      (I - A) xs - B us = Bd dhat
      H C xs = rsp - H Cd dhat

    Objective:
      1/2 |us - usp|^2_Rs + 1/2 |C xs + Cd dhat - ysp|^2_Qs
    """
    A, B, C, Bd, Cd, H = case.A, case.B, case.C, case.Bd, case.Cd, case.H
    ysp, rsp, usp, Qs, Rs = case.ysp, case.rsp, case.usp, case.Qs, case.Rs
    n, m = B.shape

    M = np.block([
        [np.eye(n) - A, -B],
        [H @ C, np.zeros((H.shape[0], m))],
    ])
    b = np.concatenate([Bd @ dhat, rsp - H @ Cd @ dhat])

    Hess = np.block([
        [C.T @ Qs @ C, np.zeros((n, m))],
        [np.zeros((m, n)), Rs],
    ])
    grad = np.concatenate([
        C.T @ Qs @ (Cd @ dhat - ysp),
        -Rs @ usp,
    ])

    KKT = np.block([
        [Hess, M.T],
        [M, np.zeros((M.shape[0], M.shape[0]))],
    ])
    rhs = np.concatenate([-grad, b])
    sol, *_ = np.linalg.lstsq(KKT, rhs, rcond=None)
    z = sol[: n + m]
    lam = sol[n + m :]
    xs = z[:n]
    us = z[n:]
    ys = C @ xs + Cd @ dhat
    rs = H @ ys
    eq_res = M @ z - b
    stationarity = Hess @ z + grad + M.T @ lam
    obj = 0.5 * float((us - usp).T @ Rs @ (us - usp)) + 0.5 * float((ys - ysp).T @ Qs @ (ys - ysp))
    return {
        "xs": xs,
        "us": us,
        "ys": ys,
        "rs": rs,
        "M": M,
        "b": b,
        "Hess": Hess,
        "grad": grad,
        "KKT": KKT,
        "objective": obj,
        "eq_residual": eq_res,
        "stationarity_residual": stationarity,
        "kkt_condition": float(np.linalg.cond(KKT)),
        "rank_M": int(matrix_rank(M)),
        "rank_augmented": int(matrix_rank(np.column_stack([M, b]))),
    }


def simulate_case(case: DisturbanceCase) -> dict[str, Any]:
    A, B, C, Bd, Cd, H = case.A, case.B, case.C, case.Bd, case.Cd, case.H
    n, m = B.shape
    p = C.shape[0]
    nd = Bd.shape[1]

    P_lqr, K_lqr, Acl, eig_acl, rho_acl = lqr_gain(A, B, case.Q_lqr, case.R_lqr)
    Az, Bz, Cz, P_est, L_est, rho_est = augmented_estimator_gain(A, B, C, Bd, Cd, case.Qe, case.Re)

    detect_M = np.block([[np.eye(n) - A, Bd], [C, Cd]])
    detect_rank = int(matrix_rank(detect_M))

    # Naive controller target assumes d_hat = 0 forever.
    zero_d = np.zeros(nd)
    naive_target = target_selector(case, zero_d)

    # Storage.
    steps = case.steps
    x = np.zeros((steps + 1, n))
    x_naive = np.zeros((steps + 1, n))
    y = np.zeros((steps + 1, p))
    y_naive = np.zeros((steps + 1, p))
    r = np.zeros((steps + 1, H.shape[0]))
    r_naive = np.zeros((steps + 1, H.shape[0]))
    u = np.zeros((steps, m))
    u_naive = np.zeros((steps, m))
    d_true_hist = np.zeros((steps + 1, nd))
    dhat_hist = np.zeros((steps + 1, nd))
    xhat_hist = np.zeros((steps + 1, n))
    xs_hist = np.zeros((steps + 1, n))
    us_hist = np.zeros((steps + 1, m))
    output_error = np.zeros(steps + 1)
    output_error_naive = np.zeros(steps + 1)
    controlled_error = np.zeros(steps + 1)
    controlled_error_naive = np.zeros(steps + 1)

    x[0] = case.x0
    x_naive[0] = case.x0.copy()
    zhat = np.concatenate([case.xhat0, case.dhat0])

    for k in range(steps + 1):
        d_true = np.zeros(nd) if k < case.step_time else case.d_true_final
        d_true_hist[k] = d_true

        y[k] = C @ x[k] + Cd @ d_true
        y_naive[k] = C @ x_naive[k] + Cd @ d_true
        r[k] = H @ y[k]
        r_naive[k] = H @ y_naive[k]

        # Measurement update for augmented estimator.
        innovation = y[k] - Cz @ zhat
        zhat = zhat + L_est @ innovation
        xhat = zhat[:n]
        dhat = zhat[n:]
        xhat_hist[k] = xhat
        dhat_hist[k] = dhat

        target = target_selector(case, dhat)
        xs = target["xs"]
        us = target["us"]
        xs_hist[k] = xs
        us_hist[k] = us

        output_error[k] = norm(y[k] - case.ysp)
        output_error_naive[k] = norm(y_naive[k] - case.ysp)
        controlled_error[k] = norm(r[k] - case.rsp)
        controlled_error_naive[k] = norm(r_naive[k] - case.rsp)

        if k < steps:
            # Offset-free controller uses estimated state and estimated disturbance-aware target.
            u[k] = us + K_lqr @ (xhat - xs)
            # Naive controller ignores the disturbance and regulates around the d=0 target.
            u_naive[k] = naive_target["us"] + K_lqr @ (x_naive[k] - naive_target["xs"])

            x[k + 1] = A @ x[k] + B @ u[k] + Bd @ d_true
            x_naive[k + 1] = A @ x_naive[k] + B @ u_naive[k] + Bd @ d_true
            zhat = Az @ zhat + Bz @ u[k]

    return {
        "P_lqr": P_lqr,
        "K_lqr": K_lqr,
        "Acl": Acl,
        "eig_acl": eig_acl,
        "rho_acl": rho_acl,
        "Az": Az,
        "Bz": Bz,
        "Cz": Cz,
        "P_est": P_est,
        "L_est": L_est,
        "rho_est": rho_est,
        "detect_M": detect_M,
        "detect_rank": detect_rank,
        "detect_required": n + nd,
        "naive_target": naive_target,
        "final_target": target_selector(case, dhat_hist[-1]),
        "x": x,
        "x_naive": x_naive,
        "y": y,
        "y_naive": y_naive,
        "r": r,
        "r_naive": r_naive,
        "u": u,
        "u_naive": u_naive,
        "d_true": d_true_hist,
        "dhat": dhat_hist,
        "xhat": xhat_hist,
        "xs": xs_hist,
        "us": us_hist,
        "output_error": output_error,
        "output_error_naive": output_error_naive,
        "controlled_error": controlled_error,
        "controlled_error_naive": controlled_error_naive,
    }


def write_case_csv(out_dir: Path, case: DisturbanceCase, res: dict[str, Any]) -> Path:
    path = out_dir / f"{case.name}_trajectory.csv"
    n = case.A.shape[0]
    m = case.B.shape[1]
    p = case.C.shape[0]
    nd = case.Bd.shape[1]
    nc = case.H.shape[0]
    steps = case.steps

    headers = ["k"]
    headers += [f"x{i+1}" for i in range(n)]
    headers += [f"x_naive{i+1}" for i in range(n)]
    headers += [f"xhat{i+1}" for i in range(n)]
    headers += [f"xs{i+1}" for i in range(n)]
    headers += [f"y{i+1}" for i in range(p)]
    headers += [f"y_naive{i+1}" for i in range(p)]
    headers += [f"r{i+1}" for i in range(nc)]
    headers += [f"r_naive{i+1}" for i in range(nc)]
    headers += [f"u{i+1}" for i in range(m)]
    headers += [f"u_naive{i+1}" for i in range(m)]
    headers += [f"us{i+1}" for i in range(m)]
    headers += [f"d_true{i+1}" for i in range(nd)]
    headers += [f"dhat{i+1}" for i in range(nd)]
    headers += ["output_error", "output_error_naive", "controlled_error", "controlled_error_naive"]

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for k in range(steps + 1):
            row: list[Any] = [k]
            row += list(res["x"][k])
            row += list(res["x_naive"][k])
            row += list(res["xhat"][k])
            row += list(res["xs"][k])
            row += list(res["y"][k])
            row += list(res["y_naive"][k])
            row += list(res["r"][k])
            row += list(res["r_naive"][k])
            if k < steps:
                row += list(res["u"][k])
                row += list(res["u_naive"][k])
            else:
                row += [math.nan] * m
                row += [math.nan] * m
            row += list(res["us"][k])
            row += list(res["d_true"][k])
            row += list(res["dhat"][k])
            row += [res["output_error"][k], res["output_error_naive"][k], res["controlled_error"][k], res["controlled_error_naive"][k]]
            writer.writerow([f"{v:.12g}" if isinstance(v, (float, np.floating)) and np.isfinite(v) else v for v in row])
    return path


def plot_case(out_dir: Path, case: DisturbanceCase, res: dict[str, Any]) -> list[Path]:
    import matplotlib.pyplot as plt

    paths: list[Path] = []
    k = np.arange(case.steps + 1)
    ku = np.arange(case.steps)

    # Output / controlled variable tracking comparison.
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for i in range(case.ysp.size):
        ax.plot(k, res["y"][:, i], label=f"offset-free y{i+1}")
        ax.plot(k, res["y_naive"][:, i], linestyle="--", label=f"naive y{i+1}")
        ax.axhline(case.ysp[i], linestyle=":", label=f"ysp{i+1}")
    ax.axvline(case.step_time, linestyle=":", label="disturbance step")
    ax.set_title(f"{case.name}: output tracking and offset comparison")
    ax.set_xlabel("k")
    ax.set_ylabel("output")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc="best")
    fig.tight_layout()
    path = out_dir / f"{case.name}_outputs.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    paths.append(path)

    # Controlled variable error.
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.semilogy(k, np.maximum(res["controlled_error"], 1e-14), label="offset-free ||r-rsp||")
    ax.semilogy(k, np.maximum(res["controlled_error_naive"], 1e-14), linestyle="--", label="naive ||r-rsp||")
    ax.axvline(case.step_time, linestyle=":", label="disturbance step")
    ax.set_title(f"{case.name}: controlled-variable offset")
    ax.set_xlabel("k")
    ax.set_ylabel("error norm, log scale")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc="best")
    fig.tight_layout()
    path = out_dir / f"{case.name}_controlled_error.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    paths.append(path)

    # Disturbance estimate.
    fig, ax = plt.subplots(figsize=(10, 5))
    for j in range(case.d_true_final.size):
        ax.plot(k, res["d_true"][:, j], label=f"true d{j+1}")
        ax.plot(k, res["dhat"][:, j], linestyle="--", label=f"estimated d{j+1}")
    ax.axvline(case.step_time, linestyle=":", label="disturbance step")
    ax.set_title(f"{case.name}: integrating disturbance estimate")
    ax.set_xlabel("k")
    ax.set_ylabel("disturbance")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc="best")
    fig.tight_layout()
    path = out_dir / f"{case.name}_disturbance_estimate.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    paths.append(path)

    # Inputs.
    fig, ax = plt.subplots(figsize=(10, 5))
    for j in range(case.B.shape[1]):
        ax.step(ku, res["u"][:, j], where="post", label=f"offset-free u{j+1}")
        ax.step(ku, res["u_naive"][:, j], where="post", linestyle="--", label=f"naive u{j+1}")
        ax.plot(k, res["us"][:, j], linestyle=":", label=f"target us{j+1}")
    ax.axvline(case.step_time, linestyle=":", label="disturbance step")
    ax.set_title(f"{case.name}: manipulated input")
    ax.set_xlabel("k")
    ax.set_ylabel("u")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc="best")
    fig.tight_layout()
    path = out_dir / f"{case.name}_inputs.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    paths.append(path)

    return paths


def make_log(cases: list[DisturbanceCase], results: dict[str, dict[str, Any]]) -> str:
    lines: list[str] = []
    lines.append("Disturbances and Zero Offset - Calculation Log")
    lines.append("Rawlings / Mayne / Diehl Section 1.5.2 sandbox")
    lines.append("")
    lines.append("Core idea")
    lines.append("  A standard tracking regulator can settle with offset when the plant has")
    lines.append("  an unmeasured constant disturbance.")
    lines.append("  Section 1.5.2 adds an integrating disturbance model d(k+1)=d(k)+wd(k).")
    lines.append("  The estimator estimates [x; d]. The target selector uses d_hat to move")
    lines.append("  the steady-state target so that the controlled variables have zero offset.")
    lines.append("  The dynamic regulator is still the old deviation regulator:")
    lines.append("    u = us(d_hat) + K * (x_hat - xs(d_hat)).")
    lines.append("")

    for case in cases:
        res = results[case.name]
        n = case.A.shape[0]
        p = case.C.shape[0]
        nd = case.Bd.shape[1]
        lines.append("=" * 92)
        lines.append(f"Case: {case.name}")
        lines.append(case.description)
        lines.append("")
        lines.append("Plant with constant disturbance")
        lines.append("  x(k+1) = A x(k) + B u(k) + Bd d(k)")
        lines.append("  y(k)   = C x(k) + Cd d(k)")
        lines.append("  d(k) is zero before the step and constant after the step.")
        lines.append(f"  n={n}, p={p}, nd={nd}")
        lines.append(f"  A =\n{fmt_mat(case.A)}")
        lines.append(f"  B =\n{fmt_mat(case.B)}")
        lines.append(f"  C =\n{fmt_mat(case.C)}")
        lines.append(f"  Bd =\n{fmt_mat(case.Bd)}")
        lines.append(f"  Cd =\n{fmt_mat(case.Cd)}")
        lines.append(f"  H =\n{fmt_mat(case.H)}")
        lines.append(f"  ysp = {fmt_vec(case.ysp)}")
        lines.append(f"  rsp = {fmt_vec(case.rsp)}")
        lines.append(f"  usp = {fmt_vec(case.usp)}")
        lines.append(f"  disturbance step time = {case.step_time}")
        lines.append(f"  final true disturbance d = {fmt_vec(case.d_true_final)}")
        lines.append("")
        lines.append("Augmented disturbance model, equations 1.42 and 1.43")
        lines.append("  d(k+1) = d(k) + wd(k)")
        lines.append("  [x; d](k+1) = [[A, Bd], [0, I]] [x; d](k) + [B; 0] u(k) + w(k)")
        lines.append("  y(k) = [C, Cd] [x; d](k) + v(k)")
        lines.append(f"  A_aug =\n{fmt_mat(res['Az'])}")
        lines.append(f"  C_aug =\n{fmt_mat(res['Cz'])}")
        lines.append("")
        lines.append("Lemma 1.8 detectability rank check")
        lines.append("  Need rank([[I-A, Bd], [C, Cd]]) = n + nd.")
        lines.append(f"  rank matrix =\n{fmt_mat(res['detect_M'])}")
        lines.append(f"  rank = {res['detect_rank']} / {res['detect_required']}")
        lines.append(f"  passes rank condition? {res['detect_rank'] == res['detect_required']}")
        lines.append(f"  Corollary 1.9 dimension check: nd={nd} <= p={p}? {nd <= p}")
        lines.append("")
        lines.append("Augmented estimator")
        lines.append(f"  Estimator process covariance Qe =\n{fmt_mat(case.Qe)}")
        lines.append(f"  Estimator measurement covariance Re =\n{fmt_mat(case.Re)}")
        lines.append(f"  Steady estimator covariance P =\n{fmt_mat(res['P_est'])}")
        lines.append(f"  Estimator gain L =\n{fmt_mat(res['L_est'])}")
        lines.append(f"  spectral radius of estimator error matrix = {res['rho_est']:.12g}")
        lines.append(f"  estimator stable? {res['rho_est'] < 1.0}")
        lines.append("")
        lines.append("Disturbance-aware target equations, equation 1.45 simplified")
        lines.append("  Steady state with estimated disturbance:")
        lines.append("    (I - A) xs - B us = Bd d_hat")
        lines.append("  Controlled-variable target with estimated disturbance:")
        lines.append("    H C xs = rsp - H Cd d_hat")
        lines.append("  Objective used:")
        lines.append("    min 1/2 |us-usp|^2_Rs + 1/2 |Cxs + Cd d_hat - ysp|^2_Qs")
        lines.append("")
        nt = res["naive_target"]
        ft = res["final_target"]
        lines.append("Naive target if d_hat = 0")
        lines.append(f"  xs0 = {fmt_vec(nt['xs'])}")
        lines.append(f"  us0 = {fmt_vec(nt['us'])}")
        lines.append(f"  y target predicted without disturbance = {fmt_vec(nt['ys'])}")
        lines.append(f"  equality residual norm = {norm(nt['eq_residual']):.12e}")
        lines.append("")
        lines.append("Final disturbance-aware target using final d_hat")
        lines.append(f"  final d_hat = {fmt_vec(res['dhat'][-1])}")
        lines.append(f"  xs(d_hat) = {fmt_vec(ft['xs'])}")
        lines.append(f"  us(d_hat) = {fmt_vec(ft['us'])}")
        lines.append(f"  ys(d_hat) = {fmt_vec(ft['ys'])}")
        lines.append(f"  rs(d_hat) = {fmt_vec(ft['rs'])}")
        lines.append(f"  target objective = {ft['objective']:.12g}")
        lines.append(f"  equality residual = {fmt_vec(ft['eq_residual'])}")
        lines.append(f"  ||equality residual|| = {norm(ft['eq_residual']):.12e}")
        lines.append(f"  KKT residual norm = {norm(ft['stationarity_residual']):.12e}")
        lines.append(f"  KKT condition number = {ft['kkt_condition']:.12e}")
        lines.append("")
        lines.append("Deviation regulator")
        lines.append("  Regulate xe = x_hat - xs(d_hat), ue = u - us(d_hat).")
        lines.append("  Same deterministic pair (A, B) is used for the regulator.")
        lines.append(f"  Riccati P =\n{fmt_mat(res['P_lqr'])}")
        lines.append(f"  K for ue = K xe =\n{fmt_mat(res['K_lqr'])}")
        lines.append(f"  A + B K =\n{fmt_mat(res['Acl'])}")
        lines.append(f"  eig(A + B K) = {fmt_vec(res['eig_acl'])}")
        lines.append(f"  spectral radius = {res['rho_acl']:.12g}")
        lines.append(f"  regulator stable? {res['rho_acl'] < 1.0}")
        lines.append("")
        lines.append("Closed-loop result: offset-free controller versus naive tracking controller")
        lines.append(f"  final offset-free x = {fmt_vec(res['x'][-1])}")
        lines.append(f"  final offset-free y = {fmt_vec(res['y'][-1])}")
        lines.append(f"  final offset-free r = {fmt_vec(res['r'][-1])}")
        lines.append(f"  final offset-free u = {fmt_vec(res['u'][-1]) if case.steps > 0 else 'n/a'}")
        lines.append(f"  final offset-free ||y-ysp|| = {res['output_error'][-1]:.12e}")
        lines.append(f"  final offset-free ||r-rsp|| = {res['controlled_error'][-1]:.12e}")
        lines.append(f"  final naive x = {fmt_vec(res['x_naive'][-1])}")
        lines.append(f"  final naive y = {fmt_vec(res['y_naive'][-1])}")
        lines.append(f"  final naive r = {fmt_vec(res['r_naive'][-1])}")
        lines.append(f"  final naive u = {fmt_vec(res['u_naive'][-1]) if case.steps > 0 else 'n/a'}")
        lines.append(f"  final naive ||y-ysp|| = {res['output_error_naive'][-1]:.12e}")
        lines.append(f"  final naive ||r-rsp|| = {res['controlled_error_naive'][-1]:.12e}")
        lines.append("")
        lines.append("Selected simulation rows")
        selected = sorted(set([0, 1, 2, case.step_time - 1, case.step_time, case.step_time + 1, case.step_time + 5, case.steps - 3, case.steps - 2, case.steps - 1, case.steps]))
        for k in selected:
            if 0 <= k <= case.steps:
                u_str = fmt_vec(res['u'][k]) if k < case.steps else "n/a"
                un_str = fmt_vec(res['u_naive'][k]) if k < case.steps else "n/a"
                lines.append(
                    f"  k={k:2d}: d={fmt_vec(res['d_true'][k])}, dhat={fmt_vec(res['dhat'][k])}, "
                    f"y={fmt_vec(res['y'][k])}, y_naive={fmt_vec(res['y_naive'][k])}, "
                    f"u={u_str}, u_naive={un_str}, "
                    f"||r-rsp||={res['controlled_error'][k]:.6g}, naive={res['controlled_error_naive'][k]:.6g}"
                )
        lines.append("")
        lines.append("Engineering interpretation")
        lines.append("  The naive controller stabilizes the plant around a target computed for d=0.")
        lines.append("  After a constant disturbance appears, that target is wrong, so the plant")
        lines.append("  can settle with a nonzero controlled-variable offset.")
        lines.append("  The offset-free controller estimates the constant disturbance and moves")
        lines.append("  xs and us so the steady-state output/controlled variable matches the setpoint.")
        lines.append("")

    return "\n".join(lines)


def jsonable(x: Any) -> Any:
    if isinstance(x, np.ndarray):
        if np.iscomplexobj(x):
            return [[float(z.real), float(z.imag)] for z in x.reshape(-1)] if x.ndim == 1 else [[complex(v) for v in row] for row in x]
        return x.tolist()
    if isinstance(x, (np.floating, np.integer)):
        return x.item()
    if isinstance(x, complex):
        return [float(x.real), float(x.imag)]
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k, v in x.items() if k not in {"KKT", "Hess", "grad"}}
    if isinstance(x, list):
        return [jsonable(v) for v in x]
    return x


def main() -> int:
    out_dir = Path(__file__).resolve().parent / "out" / "disturbances"
    out_dir.mkdir(parents=True, exist_ok=True)

    cases = [
        DisturbanceCase(
            name="output_disturbance_zero_offset",
            description=(
                "First-order plant with an additive output disturbance. The naive controller "
                "drives the internal state to x=1, but the measured output is y=x+d. "
                "The offset-free controller estimates d and moves the state target to x=1-d."
            ),
            A=arr([[0.8]]),
            B=arr([[0.2]]),
            C=arr([[1.0]]),
            Bd=arr([[0.0]]),
            Cd=arr([[1.0]]),
            H=arr([[1.0]]),
            ysp=arr([1.0]),
            rsp=arr([1.0]),
            usp=arr([0.0]),
            d_true_final=arr([0.6]),
            step_time=12,
            x0=arr([0.0]),
            xhat0=arr([0.0]),
            dhat0=arr([0.0]),
            Q_lqr=arr([[2.0]]),
            R_lqr=arr([[0.25]]),
            Qs=arr([[20.0]]),
            Rs=arr([[1.0]]),
            Qe=arr([[0.01, 0.0], [0.0, 0.005]]),
            Re=arr([[0.04]]),
            steps=70,
        ),
        DisturbanceCase(
            name="state_disturbance_zero_offset",
            description=(
                "First-order plant with an additive state disturbance. The disturbance pushes "
                "the process every sample. A naive tracking controller stabilizes at the wrong "
                "state. The offset-free controller estimates the disturbance and changes the "
                "steady input needed to hold y=1."
            ),
            A=arr([[0.8]]),
            B=arr([[0.2]]),
            C=arr([[1.0]]),
            Bd=arr([[1.0]]),
            Cd=arr([[0.0]]),
            H=arr([[1.0]]),
            ysp=arr([1.0]),
            rsp=arr([1.0]),
            usp=arr([0.0]),
            d_true_final=arr([0.1]),
            step_time=12,
            x0=arr([0.0]),
            xhat0=arr([0.0]),
            dhat0=arr([0.0]),
            Q_lqr=arr([[2.0]]),
            R_lqr=arr([[0.25]]),
            Qs=arr([[20.0]]),
            Rs=arr([[1.0]]),
            Qe=arr([[0.01, 0.0], [0.0, 0.002]]),
            Re=arr([[0.04]]),
            steps=70,
        ),
    ]

    results: dict[str, dict[str, Any]] = {}
    files: dict[str, list[str] | str] = {"plots": [], "csv": []}
    for case in cases:
        res = simulate_case(case)
        results[case.name] = res
        csv_path = write_case_csv(out_dir, case, res)
        files["csv"].append(str(csv_path))  # type: ignore[index]
        plot_paths = plot_case(out_dir, case, res)
        for p in plot_paths:
            files["plots"].append(str(p))  # type: ignore[index]

    log_text = make_log(cases, results)
    log_path = out_dir / "disturbances_calculation_log.txt"
    log_path.write_text(log_text + "\n", encoding="utf-8")
    files["log"] = str(log_path)

    summary: dict[str, Any] = {
        "title": "Rawlings Section 1.5.2 disturbances and zero offset sandbox",
        "out_dir": str(out_dir),
        "cases": {},
        "files": files,
    }
    for case in cases:
        res = results[case.name]
        summary["cases"][case.name] = {
            "description": case.description,
            "detectability_rank": res["detect_rank"],
            "detectability_required": res["detect_required"],
            "detectability_pass": res["detect_rank"] == res["detect_required"],
            "nd_le_p": case.Bd.shape[1] <= case.C.shape[0],
            "K_lqr": res["K_lqr"],
            "rho_regulator": res["rho_acl"],
            "L_estimator": res["L_est"],
            "rho_estimator": res["rho_est"],
            "true_disturbance_final": case.d_true_final,
            "estimated_disturbance_final": res["dhat"][-1],
            "naive_target": res["naive_target"],
            "final_target": res["final_target"],
            "final_offset_free_y": res["y"][-1],
            "final_naive_y": res["y_naive"][-1],
            "final_offset_free_r": res["r"][-1],
            "final_naive_r": res["r_naive"][-1],
            "final_offset_free_controlled_error": res["controlled_error"][-1],
            "final_naive_controlled_error": res["controlled_error_naive"][-1],
        }
    summary_path = out_dir / "disturbances_summary.json"
    summary_path.write_text(json.dumps(jsonable(summary), indent=2), encoding="utf-8")
    files["summary_json"] = str(summary_path)

    print("Disturbances and zero offset sandbox complete.")
    print(f"Output directory: {out_dir}")
    print(f"Log: {log_path}")
    print(f"Summary: {summary_path}")
    for case in cases:
        res = results[case.name]
        print(f"\n{case.name}")
        print(f"  final d true / d_hat: {fmt_vec(res['d_true'][-1])} / {fmt_vec(res['dhat'][-1])}")
        print(f"  final offset-free y: {fmt_vec(res['y'][-1])}")
        print(f"  final naive y:       {fmt_vec(res['y_naive'][-1])}")
        print(f"  final offset-free ||r-rsp||: {res['controlled_error'][-1]:.6e}")
        print(f"  final naive ||r-rsp||:       {res['controlled_error_naive'][-1]:.6e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
