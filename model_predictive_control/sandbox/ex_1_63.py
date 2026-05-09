#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exercise 1.63 - System identification of the nonlinear CSTR.

Rawlings, Mayne, Diehl, Model Predictive Control, Chapter 1.

This script replaces the MATLAB idinput/iddata/ssest workflow with a
self-contained Python sandbox:

1. Generate two uncorrelated PRBS input sequences around the nominal CSTR
   operating point.
2. Simulate the nonlinear CSTR from Example 1.11.
3. Add measurement noise to create a realistic identification dataset.
4. Identify a third-order, two-input, three-output discrete state-space model.
   Because all three states are measured in Example 1.11, the identified
   model uses the measured deviation states directly and estimates A and B by
   one-step weighted least squares.
5. Compare step responses of the identified model, the textbook linear model,
   and the nonlinear plant.
6. Use the identified model in an offset-free unconstrained MPC simulation with
   three integrating disturbances and the nonlinear CSTR as the plant.

Outputs are written to out/ex_1_63 by default.
"""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import solve_discrete_are

import matplotlib.pyplot as plt


Array = NDArray[np.float64]


@dataclass(frozen=True)
class CSTRParams:
    F0: float = 0.1          # m^3/min
    T0: float = 350.0        # K
    c0: float = 1.0          # kmol/m^3
    r: float = 0.219         # m
    k0: float = 7.2e10       # 1/min
    EoverR: float = 8750.0   # K
    U: float = 54.94         # kJ/(min m^2 K)
    rho: float = 1000.0      # kg/m^3
    Cp: float = 0.239        # kJ/(kg K)
    dH: float = -5.0e4       # kJ/kmol


# Nominal steady state and textbook discrete linear model from Example 1.11.
XS = np.array([0.878, 324.5, 0.659], dtype=float)  # [c, T, h]
US = np.array([300.0, 0.1], dtype=float)           # [Tc, F]

A_TEXTBOOK = np.array(
    [
        [0.2681, -0.00338, -0.00728],
        [9.703, 0.3279, -25.44],
        [0.0, 0.0, 1.0],
    ],
    dtype=float,
)
B_TEXTBOOK = np.array(
    [
        [-0.00537, 0.1655],
        [1.297, 97.91],
        [0.0, -6.637],
    ],
    dtype=float,
)
BP_TEXTBOOK = np.array([-0.1175, 69.74, 6.637], dtype=float)
C_TEXTBOOK = np.eye(3, dtype=float)

STATE_NAMES = ["c_minus_cs_kmol_m3", "T_minus_Ts_K", "h_minus_hs_m"]
INPUT_NAMES = ["Tc_minus_Tcs_K", "F_minus_Fs_m3_min"]
OUTPUT_ABS_NAMES = ["c_kmol_m3", "T_K", "h_m"]
INPUT_ABS_NAMES = ["Tc_K", "F_m3_min"]


def cstr_rhs(x_abs: Array, u_abs: Array, params: CSTRParams, F0: float | None = None, U: float | None = None) -> Array:
    """Continuous-time nonlinear CSTR right-hand side in absolute variables."""

    c, T, h = np.asarray(x_abs, dtype=float)
    Tc, F = np.asarray(u_abs, dtype=float)
    F0_eff = params.F0 if F0 is None else float(F0)
    U_eff = params.U if U is None else float(U)

    area = np.pi * params.r**2
    h_safe = max(float(h), 1.0e-4)
    k = params.k0 * np.exp(-params.EoverR / max(float(T), 1.0))

    dc = F0_eff * (params.c0 - c) / (area * h_safe) - k * c
    dT = (
        F0_eff * (params.T0 - T) / (area * h_safe)
        + (-params.dH) / (params.rho * params.Cp) * k * c
        + 2.0 * U_eff / (params.r * params.rho * params.Cp) * (Tc - T)
    )
    dh = (F0_eff - F) / area
    return np.array([dc, dT, dh], dtype=float)


def rk4_step(x_abs: Array, u_abs: Array, dt: float, params: CSTRParams, *, F0: float | None = None, U: float | None = None, substeps: int = 20) -> Array:
    """Integrate the nonlinear CSTR for one sample using fixed-step RK4."""

    h = dt / int(substeps)
    x = np.asarray(x_abs, dtype=float).copy()
    for _ in range(int(substeps)):
        k1 = cstr_rhs(x, u_abs, params, F0=F0, U=U)
        k2 = cstr_rhs(x + 0.5 * h * k1, u_abs, params, F0=F0, U=U)
        k3 = cstr_rhs(x + 0.5 * h * k2, u_abs, params, F0=F0, U=U)
        k4 = cstr_rhs(x + h * k3, u_abs, params, F0=F0, U=U)
        x = x + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        x[2] = max(x[2], 1.0e-4)
    return x


def generate_prbs(n_samples: int, amp: float, rng: np.random.Generator, min_block: int = 3, max_block: int = 12) -> Array:
    """Generate a simple PRBS-like binary signal with random block lengths."""

    values: list[float] = []
    current = amp if rng.random() > 0.5 else -amp
    while len(values) < n_samples:
        if rng.random() < 0.65:
            current = -current
        block = int(rng.integers(min_block, max_block + 1))
        values.extend([current] * block)
    return np.asarray(values[:n_samples], dtype=float)


def make_identification_data(n_samples: int, dt: float, rng: np.random.Generator, params: CSTRParams) -> dict[str, Array]:
    """Generate PRBS inputs and noisy nonlinear CSTR outputs."""

    # Conservative local perturbations to avoid ignition/nonlinear branch changes.
    u_dev = np.column_stack(
        [
            generate_prbs(n_samples, amp=0.2, rng=rng, min_block=1, max_block=5),       # coolant temperature, K
            generate_prbs(n_samples, amp=0.0002, rng=rng, min_block=1, max_block=5),    # outlet flowrate, m^3/min
        ]
    )

    x_abs = np.zeros((n_samples + 1, 3), dtype=float)
    y_dev_clean = np.zeros((n_samples + 1, 3), dtype=float)
    x_abs[0] = XS.copy()
    y_dev_clean[0] = x_abs[0] - XS

    for k in range(n_samples):
        u_abs = US + u_dev[k]
        x_abs[k + 1] = rk4_step(x_abs[k], u_abs, dt, params, substeps=20)
        y_dev_clean[k + 1] = x_abs[k + 1] - XS

    # Measurement noise. These are intentionally small enough for local ID but visible.
    noise_std = np.array([4.0e-4, 4.0e-2, 4.0e-4], dtype=float)
    noise = rng.normal(0.0, noise_std, size=y_dev_clean.shape)
    y_dev_noisy = y_dev_clean + noise
    y_dev_noisy[0] = y_dev_clean[0] + rng.normal(0.0, noise_std)

    return {
        "u_dev": u_dev,
        "x_abs": x_abs,
        "y_dev_clean": y_dev_clean,
        "y_dev_noisy": y_dev_noisy,
        "noise_std": noise_std,
        "time": np.arange(n_samples + 1, dtype=float) * dt,
    }


def identify_measured_state_model(y_dev: Array, u_dev: Array, ridge: float = 1.0e-8) -> tuple[Array, Array]:
    """Identify x+ = A x + B u using measured outputs as states.

    This is a Python replacement for a simple third-order ssest workflow. Since
    Example 1.11 measures all three states, the measured outputs are legitimate
    state coordinates for this sandbox.
    """

    xk = y_dev[:-1]
    xkp1 = y_dev[1:]
    uk = u_dev
    phi = np.hstack([xk, uk])  # n_samples x 5
    gram = phi.T @ phi + ridge * np.eye(phi.shape[1])
    theta = np.linalg.solve(gram, phi.T @ xkp1)  # 5 x 3, predicts rows
    A_id = theta[:3, :].T
    B_id = theta[3:, :].T
    return A_id, B_id


def simulate_discrete_model(A: Array, B: Array, u_dev: Array, x0_dev: Array | None = None) -> Array:
    """Simulate a discrete deviation model."""

    n = u_dev.shape[0]
    x = np.zeros((n + 1, A.shape[0]), dtype=float)
    if x0_dev is not None:
        x[0] = x0_dev
    for k in range(n):
        x[k + 1] = A @ x[k] + B @ u_dev[k]
    return x


def step_test_models(A_id: Array, B_id: Array, dt: float, params: CSTRParams) -> dict[str, Array]:
    """Step-test nonlinear plant, textbook model, and identified model."""

    n_steps = 40
    cases = [
        ("Tc +1 K", np.array([1.0, 0.0], dtype=float)),
        ("F +0.0002 m3/min", np.array([0.0, 0.0002], dtype=float)),
    ]
    out: dict[str, Array] = {"time": np.arange(n_steps + 1, dtype=float) * dt}

    for label, step in cases:
        u = np.repeat(step.reshape(1, 2), n_steps, axis=0)
        nonlinear = np.zeros((n_steps + 1, 3), dtype=float)
        x_abs = XS.copy()
        nonlinear[0] = x_abs - XS
        for k in range(n_steps):
            x_abs = rk4_step(x_abs, US + step, dt, params, substeps=20)
            nonlinear[k + 1] = x_abs - XS
        out[f"{label} nonlinear"] = nonlinear
        out[f"{label} textbook"] = simulate_discrete_model(A_TEXTBOOK, B_TEXTBOOK, u)
        out[f"{label} identified"] = simulate_discrete_model(A_id, B_id, u)

    return out


def prediction_matrices(A: Array, B: Array, horizon: int) -> tuple[Array, Array]:
    """Build stacked prediction matrices for x_i, i=1..N."""

    nx, nu = B.shape
    sx = np.zeros((horizon * nx, nx), dtype=float)
    su = np.zeros((horizon * nx, horizon * nu), dtype=float)
    powers = [np.eye(nx)]
    for i in range(1, horizon + 1):
        powers.append(powers[-1] @ A)
    for i in range(1, horizon + 1):
        sx[(i - 1) * nx : i * nx, :] = powers[i]
        for j in range(i):
            su[(i - 1) * nx : i * nx, j * nu : (j + 1) * nu] = powers[i - 1 - j] @ B
    return sx, su


def unconstrained_mpc_first_move(A: Array, B: Array, e0: Array, horizon: int, Q: Array, R: Array, P: Array) -> Array:
    """Solve unconstrained finite-horizon regulation and return first input move."""

    nx, nu = B.shape
    sx, su = prediction_matrices(A, B, horizon)
    q_blocks = [Q for _ in range(horizon - 1)] + [P]
    qbar = block_diag(q_blocks)
    rbar = block_diag([R for _ in range(horizon)])
    hess = su.T @ qbar @ su + rbar
    grad = su.T @ qbar @ (sx @ e0)
    u_stack = -np.linalg.solve(hess + 1.0e-10 * np.eye(hess.shape[0]), grad)
    return u_stack[:nu]


def block_diag(blocks: Iterable[Array]) -> Array:
    """Small local block diagonal helper to avoid depending on scipy for this."""

    blocks = list(blocks)
    rows = sum(b.shape[0] for b in blocks)
    cols = sum(b.shape[1] for b in blocks)
    out = np.zeros((rows, cols), dtype=float)
    r = c = 0
    for b in blocks:
        rr, cc = b.shape
        out[r : r + rr, c : c + cc] = b
        r += rr
        c += cc
    return out


def steady_target(A: Array, B: Array, Bd: Array, C: Array, Cd: Array, d_hat: Array, controlled_indices: list[int], r_sp: Array, u_sp: Array) -> tuple[Array, Array, Array]:
    """Compute least-norm steady target for given disturbance estimate."""

    nx, nu = B.shape
    H = np.zeros((len(controlled_indices), C.shape[0]), dtype=float)
    for row, idx in enumerate(controlled_indices):
        H[row, idx] = 1.0

    # Equations:
    # (I-A)x - B u = Bd d
    # H(Cx + Cd d) = r_sp
    M = np.block([[np.eye(nx) - A, -B], [H @ C, np.zeros((len(controlled_indices), nu))]])
    rhs = np.concatenate([Bd @ d_hat, r_sp - H @ Cd @ d_hat])

    # Minimize ||u-u_sp||^2 subject to M [x;u] = rhs.
    # Since there are generally more equations than inputs, compute a feasible
    # least-squares solution and then use the nullspace to minimize u deviation.
    z0 = np.linalg.lstsq(M, rhs, rcond=None)[0]
    # Nullspace basis from SVD.
    _, s, vt = np.linalg.svd(M)
    rank = int(np.sum(s > 1.0e-9))
    Z = vt[rank:].T
    if Z.size:
        Eu = np.hstack([np.zeros((nu, nx)), np.eye(nu)])
        lhs = Eu @ Z
        rhs2 = u_sp - Eu @ z0
        alpha = np.linalg.lstsq(lhs, rhs2, rcond=None)[0]
        z = z0 + Z @ alpha
    else:
        z = z0

    x_s = z[:nx]
    u_s = z[nx:]
    y_s = C @ x_s + Cd @ d_hat
    return x_s, u_s, y_s


def kalman_update(xhat: Array, P: Array, y: Array, C: Array, R: Array) -> tuple[Array, Array, Array]:
    """Measurement update for a linear Gaussian estimator."""

    S = C @ P @ C.T + R
    K = P @ C.T @ np.linalg.pinv(S)
    innovation = y - C @ xhat
    xhat_new = xhat + K @ innovation
    P_new = (np.eye(P.shape[0]) - K @ C) @ P @ (np.eye(P.shape[0]) - K @ C).T + K @ R @ K.T
    return xhat_new, P_new, innovation


def simulate_offset_free_mpc_with_identified_model(A_id: Array, B_id: Array, dt: float, params: CSTRParams, rng: np.random.Generator) -> dict[str, Array]:
    """Closed-loop nonlinear CSTR simulation using identified linear model in MPC."""

    nx, nu, nd, ny = 3, 2, 3, 3
    C = np.eye(3)

    # Example 1.11(c)-style disturbance model: output disturbances on c and h,
    # plus an input disturbance in the F channel.
    Cd = np.array([[1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=float)
    Bd = np.column_stack([np.zeros(nx), np.zeros(nx), B_id[:, 1]])

    Ae = np.block([[A_id, Bd], [np.zeros((nd, nx)), np.eye(nd)]])
    Be = np.vstack([B_id, np.zeros((nd, nu))])
    Ce = np.hstack([C, Cd])

    # Estimator tuning. Small measurement noise and disturbance covariance.
    Qe = np.diag([1.0e-10, 1.0e-8, 1.0e-10, 1.0e-6, 1.0e-6, 5.0e-5])
    Re = np.diag([1.0e-8, 1.0e-6, 1.0e-8])
    P = np.diag([1.0e-4, 1.0e-1, 1.0e-4, 1.0, 1.0, 1.0])
    xhat_e = np.zeros(nx + nd, dtype=float)

    # MPC weights. Control c and h most strongly; T is left as measured but not targeted.
    Qy = np.diag([8.0, 0.05, 8.0])
    Qx = C.T @ Qy @ C
    R = np.diag([0.08, 0.08])
    Pterm = solve_discrete_are(A_id, B_id, Qx + 1.0e-9 * np.eye(nx), R)
    horizon = 12

    n_steps = 50
    x_abs = np.zeros((n_steps + 1, nx), dtype=float)
    y_abs = np.zeros((n_steps + 1, ny), dtype=float)
    y_dev = np.zeros((n_steps + 1, ny), dtype=float)
    xhat = np.zeros((n_steps + 1, nx), dtype=float)
    dhat = np.zeros((n_steps + 1, nd), dtype=float)
    u_dev = np.zeros((n_steps, nu), dtype=float)
    u_abs = np.zeros((n_steps, nu), dtype=float)
    target_x = np.zeros((n_steps, nx), dtype=float)
    target_u = np.zeros((n_steps, nu), dtype=float)
    innovation = np.zeros((n_steps + 1, ny), dtype=float)

    x_abs[0] = XS.copy()
    y_abs[0] = x_abs[0]
    y_dev[0] = y_abs[0] - XS
    r_sp = np.array([0.0, 0.0], dtype=float)  # c and h deviation targets
    controlled = [0, 2]

    for k in range(n_steps):
        # Measurement update at current sample. For this exercise use essentially
        # noise-free measurement in the closed-loop test.
        meas = x_abs[k] - XS
        xhat_e, P, innov = kalman_update(xhat_e, P, meas, Ce, Re)
        innovation[k] = innov
        xhat[k] = xhat_e[:nx]
        dhat[k] = xhat_e[nx:]

        xs_dev, us_dev, _ys_dev = steady_target(A_id, B_id, Bd, C, Cd, dhat[k], controlled, r_sp, np.zeros(nu))
        target_x[k] = xs_dev
        target_u[k] = us_dev

        e0 = xhat[k] - xs_dev
        du = unconstrained_mpc_first_move(A_id, B_id, e0, horizon, Qx, R, Pterm)
        u_dev[k] = us_dev + du

        # Conservative actuator clipping for nonlinear plant sanity.
        u_dev[k, 0] = float(np.clip(u_dev[k, 0], -15.0, 15.0))
        u_dev[k, 1] = float(np.clip(u_dev[k, 1], -0.04, 0.04))
        u_abs[k] = US + u_dev[k]

        F0_plant = params.F0 * (1.10 if (k * dt) >= 10.0 else 1.0)
        x_abs[k + 1] = rk4_step(x_abs[k], u_abs[k], dt, params, F0=F0_plant, substeps=20)
        y_abs[k + 1] = x_abs[k + 1]
        y_dev[k + 1] = y_abs[k + 1] - XS

        # Time update for the estimator.
        xhat_e = Ae @ xhat_e + Be @ u_dev[k]
        P = Ae @ P @ Ae.T + Qe

    # Final measurement update for stored final estimates.
    xhat_e, P, innov = kalman_update(xhat_e, P, y_dev[-1], Ce, Re)
    xhat[-1] = xhat_e[:nx]
    dhat[-1] = xhat_e[nx:]
    innovation[-1] = innov

    return {
        "time": np.arange(n_steps + 1, dtype=float) * dt,
        "time_u": np.arange(n_steps, dtype=float) * dt,
        "x_abs": x_abs,
        "y_abs": y_abs,
        "y_dev": y_dev,
        "u_abs": u_abs,
        "u_dev": u_dev,
        "xhat": xhat,
        "dhat": dhat,
        "target_x": target_x,
        "target_u": target_u,
        "innovation": innovation,
        "Ae_rank_condition": np.array([np.linalg.matrix_rank(np.block([[np.eye(nx) - A_id, Bd], [C, Cd]]))], dtype=float),
    }


def write_csv(path: Path, header: list[str], rows: Array) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows.tolist())


def save_json(path: Path, payload: dict) -> None:
    def convert(obj):
        if isinstance(obj, np.ndarray):
            if np.iscomplexobj(obj):
                return [{"real": float(np.real(v)), "imag": float(np.imag(v))} for v in obj.reshape(-1)] if obj.ndim == 1 else [[{"real": float(np.real(v)), "imag": float(np.imag(v))} for v in row] for row in obj]
            return obj.tolist()
        if isinstance(obj, (np.floating, np.integer)):
            return obj.item()
        if isinstance(obj, (complex, np.complexfloating)):
            return {"real": float(np.real(obj)), "imag": float(np.imag(obj))}
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [convert(v) for v in obj]
        return obj

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(convert(payload), f, indent=2)
        f.write("\n")


def plot_identification_data(out_dir: Path, data: dict[str, Array]) -> Path:
    t = data["time"]
    u = data["u_dev"]
    y = data["y_dev_noisy"]
    fig, axes = plt.subplots(5, 1, figsize=(11, 10), sharex=True)
    axes[0].step(t[:-1], u[:, 0], where="post")
    axes[0].set_ylabel("Tc dev [K]")
    axes[1].step(t[:-1], u[:, 1], where="post")
    axes[1].set_ylabel("F dev [m3/min]")
    for i, name in enumerate(["c dev", "T dev", "h dev"]):
        axes[i + 2].plot(t, y[:, i])
        axes[i + 2].set_ylabel(name)
    axes[-1].set_xlabel("time [min]")
    fig.suptitle("Exercise 1.63 identification dataset: PRBS inputs and noisy outputs")
    for ax in axes:
        ax.grid(True, alpha=0.3)
    fig.tight_layout()
    path = out_dir / "identification_data.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def plot_fit(out_dir: Path, data: dict[str, Array], A_id: Array, B_id: Array) -> Path:
    t = data["time"]
    y = data["y_dev_noisy"]
    u = data["u_dev"]
    y_id = simulate_discrete_model(A_id, B_id, u)
    y_txt = simulate_discrete_model(A_TEXTBOOK, B_TEXTBOOK, u)
    fig, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
    for i, name in enumerate(STATE_NAMES):
        axes[i].plot(t, y[:, i], label="noisy nonlinear data", alpha=0.6)
        axes[i].plot(t, y_id[:, i], label="identified one-step model")
        axes[i].plot(t, y_txt[:, i], label="textbook linear model", linestyle="--")
        axes[i].set_ylabel(name)
        axes[i].grid(True, alpha=0.3)
        axes[i].legend(fontsize=8)
    axes[-1].set_xlabel("time [min]")
    fig.suptitle("Open-loop replay fit on the identification input sequence")
    fig.tight_layout()
    path = out_dir / "identification_fit.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def plot_step_tests(out_dir: Path, steps: dict[str, Array]) -> Path:
    t = steps["time"]
    cases = ["Tc +1 K", "F +0.0002 m3/min"]
    fig, axes = plt.subplots(3, 2, figsize=(13, 8), sharex=True)
    for col, case in enumerate(cases):
        for row, name in enumerate(STATE_NAMES):
            ax = axes[row, col]
            ax.plot(t, steps[f"{case} nonlinear"][:, row], label="nonlinear plant")
            ax.plot(t, steps[f"{case} textbook"][:, row], label="textbook linear", linestyle="--")
            ax.plot(t, steps[f"{case} identified"][:, row], label="identified", linestyle=":")
            ax.set_title(case if row == 0 else "")
            ax.set_ylabel(name)
            ax.grid(True, alpha=0.3)
            if row == 0:
                ax.legend(fontsize=8)
    axes[-1, 0].set_xlabel("time [min]")
    axes[-1, 1].set_xlabel("time [min]")
    fig.suptitle("Step-test comparison: nonlinear plant vs linear models")
    fig.tight_layout()
    path = out_dir / "step_test_comparison.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def plot_closed_loop(out_dir: Path, cl: dict[str, Array]) -> tuple[Path, Path, Path]:
    t = cl["time"]
    tu = cl["time_u"]
    x = cl["x_abs"]
    u = cl["u_abs"]
    d = cl["dhat"]

    fig, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
    ylabels = ["c [kmol/m3]", "T [K]", "h [m]"]
    for i in range(3):
        axes[i].plot(t, x[:, i])
        axes[i].axhline(XS[i], linestyle="--", linewidth=1.0, label="nominal target" if i in (0, 2) else "nominal")
        axes[i].axvline(10.0, linestyle=":", linewidth=1.2, label="F0 step" if i == 0 else None)
        axes[i].set_ylabel(ylabels[i])
        axes[i].grid(True, alpha=0.3)
        axes[i].legend(fontsize=8)
    axes[-1].set_xlabel("time [min]")
    fig.suptitle("Closed-loop nonlinear CSTR with identified-model offset-free MPC")
    fig.tight_layout()
    path_y = out_dir / "closed_loop_outputs.png"
    fig.savefig(path_y, dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
    axes[0].step(tu, u[:, 0], where="post")
    axes[0].axhline(US[0], linestyle="--", linewidth=1.0)
    axes[0].set_ylabel("Tc [K]")
    axes[1].step(tu, u[:, 1], where="post")
    axes[1].axhline(US[1], linestyle="--", linewidth=1.0)
    axes[1].set_ylabel("F [m3/min]")
    axes[1].set_xlabel("time [min]")
    for ax in axes:
        ax.axvline(10.0, linestyle=":", linewidth=1.2)
        ax.grid(True, alpha=0.3)
    fig.suptitle("Manipulated inputs")
    fig.tight_layout()
    path_u = out_dir / "closed_loop_inputs.png"
    fig.savefig(path_u, dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(3, 1, figsize=(11, 7), sharex=True)
    for i in range(3):
        axes[i].plot(t, d[:, i])
        axes[i].axvline(10.0, linestyle=":", linewidth=1.2)
        axes[i].set_ylabel(f"d{i+1}")
        axes[i].grid(True, alpha=0.3)
    axes[-1].set_xlabel("time [min]")
    fig.suptitle("Estimated integrating disturbances")
    fig.tight_layout()
    path_d = out_dir / "closed_loop_disturbances.png"
    fig.savefig(path_d, dpi=160)
    plt.close(fig)

    return path_y, path_u, path_d


def rmse(a: Array, b: Array) -> Array:
    return np.sqrt(np.mean((a - b) ** 2, axis=0))


def main() -> int:
    parser = argparse.ArgumentParser(description="Exercise 1.63 nonlinear CSTR system-identification sandbox")
    parser.add_argument("--out", default=None, help="Output directory. Default: ./out/ex_1_63 relative to this file or cwd")
    parser.add_argument("--samples", type=int, default=700, help="Identification samples")
    parser.add_argument("--dt", type=float, default=1.0, help="Sample time in min")
    parser.add_argument("--seed", type=int, default=163, help="Random seed")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    out_dir = Path(args.out).expanduser().resolve() if args.out else script_dir / "out" / "ex_1_63"
    out_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(args.seed)
    params = CSTRParams()

    data = make_identification_data(args.samples, args.dt, rng, params)
    A_id, B_id = identify_measured_state_model(data["y_dev_noisy"], data["u_dev"])
    y_id = simulate_discrete_model(A_id, B_id, data["u_dev"])
    y_txt = simulate_discrete_model(A_TEXTBOOK, B_TEXTBOOK, data["u_dev"])

    steps = step_test_models(A_id, B_id, args.dt, params)
    cl = simulate_offset_free_mpc_with_identified_model(A_id, B_id, args.dt, params, rng)

    plots = {}
    plots["identification_data"] = plot_identification_data(out_dir, data)
    plots["identification_fit"] = plot_fit(out_dir, data, A_id, B_id)
    plots["step_tests"] = plot_step_tests(out_dir, steps)
    py, pu, pd = plot_closed_loop(out_dir, cl)
    plots["closed_loop_outputs"] = py
    plots["closed_loop_inputs"] = pu
    plots["closed_loop_disturbances"] = pd

    # CSV outputs.
    t = data["time"]
    rows = np.column_stack([t, data["y_dev_clean"], data["y_dev_noisy"], np.vstack([data["u_dev"], [np.nan, np.nan]])])
    write_csv(
        out_dir / "identification_dataset.csv",
        ["time", "c_clean_dev", "T_clean_dev", "h_clean_dev", "c_noisy_dev", "T_noisy_dev", "h_noisy_dev", "Tc_dev", "F_dev"],
        rows,
    )
    cl_rows = np.column_stack([cl["time"], cl["x_abs"], cl["y_dev"], cl["xhat"], cl["dhat"]])
    write_csv(
        out_dir / "closed_loop_outputs.csv",
        ["time", "c", "T", "h", "c_dev", "T_dev", "h_dev", "xhat_c_dev", "xhat_T_dev", "xhat_h_dev", "d1", "d2", "d3"],
        cl_rows,
    )
    u_rows = np.column_stack([cl["time_u"], cl["u_abs"], cl["u_dev"], cl["target_u"]])
    write_csv(
        out_dir / "closed_loop_inputs.csv",
        ["time", "Tc", "F", "Tc_dev", "F_dev", "target_Tc_dev", "target_F_dev"],
        u_rows,
    )

    # Metrics.
    fit_rmse_id = rmse(y_id, data["y_dev_clean"])
    fit_rmse_txt = rmse(y_txt, data["y_dev_clean"])
    step_metrics = {}
    for case in ["Tc +1 K", "F +0.0002 m3/min"]:
        step_metrics[case] = {
            "identified_rmse_vs_nonlinear": rmse(steps[f"{case} identified"], steps[f"{case} nonlinear"]),
            "textbook_rmse_vs_nonlinear": rmse(steps[f"{case} textbook"], steps[f"{case} nonlinear"]),
        }

    final_offsets = cl["x_abs"][-1] - XS
    result = {
        "title": "Exercise 1.63 - System identification of nonlinear CSTR",
        "sample_time_min": args.dt,
        "identification_samples": args.samples,
        "seed": args.seed,
        "nominal_state_XS": XS,
        "nominal_input_US": US,
        "params": asdict(params),
        "textbook_A": A_TEXTBOOK,
        "textbook_B": B_TEXTBOOK,
        "identified_A": A_id,
        "identified_B": B_id,
        "identified_eigenvalues": np.linalg.eigvals(A_id),
        "textbook_eigenvalues": np.linalg.eigvals(A_TEXTBOOK),
        "open_loop_replay_rmse_identified_vs_clean": fit_rmse_id,
        "open_loop_replay_rmse_textbook_vs_clean": fit_rmse_txt,
        "step_metrics": step_metrics,
        "augmented_detectability_rank_required": 6,
        "augmented_detectability_rank_observed": cl["Ae_rank_condition"],
        "closed_loop_final_offsets_absolute_minus_nominal": final_offsets,
        "closed_loop_controlled_variable_final_offsets_c_and_h": final_offsets[[0, 2]],
        "plots": {k: str(v) for k, v in plots.items()},
        "interpretation": {
            "identification": "The identified model is a 3-state measured-state realization fitted from PRBS data. It is the Python analogue of a third-order ssest workflow for this fully measured CSTR.",
            "zero_offset": "The closed-loop test uses three integrating disturbances like Example 1.11(c): output disturbances on c and h plus an input disturbance through the F channel. The rank test should be 6 for detectability.",
            "robustness_warning": "The identified model quality depends on PRBS amplitude, noise, and whether the nonlinear plant remains near the nominal operating point.",
        },
    }
    save_json(out_dir / "ex_1_63_results.json", result)

    with (out_dir / "calculation_log.txt").open("w", encoding="utf-8") as f:
        f.write("Rawlings/Mayne/Diehl MPC - Exercise 1.63 sandbox\n")
        f.write("System identification of the nonlinear CSTR from Example 1.11\n\n")
        f.write(f"Output directory: {out_dir}\n")
        f.write(f"Sample time: {args.dt} min\n")
        f.write(f"Identification samples: {args.samples}\n")
        f.write(f"Random seed: {args.seed}\n\n")
        f.write("Textbook discrete A matrix\n")
        f.write(np.array2string(A_TEXTBOOK, precision=6) + "\n\n")
        f.write("Textbook discrete B matrix\n")
        f.write(np.array2string(B_TEXTBOOK, precision=6) + "\n\n")
        f.write("Identified A matrix\n")
        f.write(np.array2string(A_id, precision=6) + "\n\n")
        f.write("Identified B matrix\n")
        f.write(np.array2string(B_id, precision=6) + "\n\n")
        f.write("Eigenvalues\n")
        f.write(f"  textbook:   {np.linalg.eigvals(A_TEXTBOOK)}\n")
        f.write(f"  identified: {np.linalg.eigvals(A_id)}\n\n")
        f.write("Open-loop replay RMSE versus clean nonlinear data [c, T, h]\n")
        f.write(f"  identified: {fit_rmse_id}\n")
        f.write(f"  textbook:   {fit_rmse_txt}\n\n")
        f.write("Step-test RMSE versus nonlinear plant\n")
        for case, metrics in step_metrics.items():
            f.write(f"  {case}\n")
            f.write(f"    identified: {metrics['identified_rmse_vs_nonlinear']}\n")
            f.write(f"    textbook:   {metrics['textbook_rmse_vs_nonlinear']}\n")
        f.write("\nOffset-free MPC closed-loop test\n")
        f.write("  disturbance: +10% inlet flowrate F0 at t = 10 min\n")
        f.write(f"  augmented detectability rank observed: {cl['Ae_rank_condition'][0]:.0f} / 6\n")
        f.write(f"  final output offsets [c-cs, T-Ts, h-hs]: {final_offsets}\n")
        f.write(f"  final controlled-variable offsets [c-cs, h-hs]: {final_offsets[[0,2]]}\n\n")
        f.write("Files written\n")
        for name, path in plots.items():
            f.write(f"  {name}: {path}\n")
        f.write("  ex_1_63_results.json\n")
        f.write("  identification_dataset.csv\n")
        f.write("  closed_loop_outputs.csv\n")
        f.write("  closed_loop_inputs.csv\n")

    print(f"Done. Wrote Exercise 1.63 outputs to: {out_dir}")
    print(f"Script: {Path(__file__).resolve()}")
    print(f"Identified A:\n{A_id}")
    print(f"Identified B:\n{B_id}")
    print(f"Final controlled offsets [c, h]: {final_offsets[[0, 2]]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
