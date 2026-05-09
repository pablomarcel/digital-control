#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exercise 1.63 - System identification of the nonlinear CSTR.

Rawlings, Mayne, Diehl, Model Predictive Control, Chapter 1.

This upgraded sandbox is intentionally diagnostic.  The previous version used
ordinary least squares directly on noisy measured outputs as if they were exact
states.  That is a classic errors-in-variables mistake: measurement noise appears
on both sides of x(k+1) = A x(k) + B u(k), so the fitted A matrix becomes biased,
especially when the PRBS amplitudes are intentionally small to keep the nonlinear
CSTR near the nominal operating point.

The script now writes and compares several models:

1. raw_noisy_ls
   The old measured-state least-squares workflow.  It is retained as a warning.

2. clean_replay_ls
   The same workflow applied to the clean simulated states.  This is not what one
   has in a real experiment, but it exposes how much of the failure came from
   measurement noise rather than the nonlinear plant.

3. local_finite_difference
   A local discrete-time perturbation model obtained by perturbing the nonlinear
   simulator around the nominal steady state and integrating one sample.

4. regularized_noise_aware
   The selected model.  It fits the noisy PRBS dataset, but regularizes toward the
   local perturbation model and enforces the physically known level integrator.
   This is a practical grey-box identification compromise for this sandbox.

The selected model is then used in an offset-free linear MPC simulation with the
nonlinear CSTR as the plant.  The closed-loop test applies a +10% inlet-flow
step at 10 minutes.  The controller targets concentration and level, matching the
spirit of the offset-free CSTR examples in Section 1.5.

Outputs are written to out/ex_1_63 by default.
"""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray
from scipy.linalg import LinAlgError, solve_discrete_are

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

STATE_NAMES = ["c-cs [kmol/m3]", "T-Ts [K]", "h-hs [m]"]
INPUT_NAMES = ["Tc-Tcs [K]", "F-Fs [m3/min]"]
ABS_STATE_NAMES = ["c [kmol/m3]", "T [K]", "h [m]"]
ABS_INPUT_NAMES = ["Tc [K]", "F [m3/min]"]


def cstr_rhs(
    x_abs: Array,
    u_abs: Array,
    params: CSTRParams,
    *,
    F0: float | None = None,
    U: float | None = None,
) -> Array:
    """Continuous-time nonlinear CSTR right-hand side in absolute variables."""

    c, T, h = np.asarray(x_abs, dtype=float)
    Tc, F = np.asarray(u_abs, dtype=float)
    F0_eff = params.F0 if F0 is None else float(F0)
    U_eff = params.U if U is None else float(U)

    area = np.pi * params.r**2
    h_safe = max(float(h), 1.0e-4)
    T_safe = max(float(T), 1.0)
    k = params.k0 * np.exp(-params.EoverR / T_safe)

    dc = F0_eff * (params.c0 - c) / (area * h_safe) - k * c
    dT = (
        F0_eff * (params.T0 - T) / (area * h_safe)
        + (-params.dH) / (params.rho * params.Cp) * k * c
        + 2.0 * U_eff / (params.r * params.rho * params.Cp) * (Tc - T)
    )
    dh = (F0_eff - F) / area
    return np.array([dc, dT, dh], dtype=float)


def rk4_step(
    x_abs: Array,
    u_abs: Array,
    dt: float,
    params: CSTRParams,
    *,
    F0: float | None = None,
    U: float | None = None,
    substeps: int = 20,
) -> Array:
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
        if not np.all(np.isfinite(x)):
            raise FloatingPointError("CSTR integration diverged; reduce excitation amplitudes.")
    return x


def generate_prbs(
    n_samples: int,
    amp: float,
    rng: np.random.Generator,
    *,
    min_block: int = 1,
    max_block: int = 5,
    switch_probability: float = 0.65,
) -> Array:
    """Generate a PRBS-like two-level sequence with random block lengths."""

    values: list[float] = []
    current = amp if rng.random() > 0.5 else -amp
    while len(values) < n_samples:
        if rng.random() < switch_probability:
            current = -current
        block = int(rng.integers(min_block, max_block + 1))
        values.extend([current] * block)
    return np.asarray(values[:n_samples], dtype=float)


def make_identification_data(
    n_samples: int,
    dt: float,
    rng: np.random.Generator,
    params: CSTRParams,
    *,
    tc_amp: float = 0.20,
    f_amp: float = 0.00020,
    noise_scale: float = 1.0,
) -> dict[str, Array]:
    """Generate PRBS inputs plus clean and noisy nonlinear CSTR outputs."""

    u_dev = np.column_stack(
        [
            generate_prbs(n_samples, tc_amp, rng, min_block=1, max_block=5),
            generate_prbs(n_samples, f_amp, rng, min_block=1, max_block=5),
        ]
    )

    x_abs = np.zeros((n_samples + 1, 3), dtype=float)
    y_dev_clean = np.zeros((n_samples + 1, 3), dtype=float)
    x_abs[0] = XS.copy()

    for k in range(n_samples):
        x_abs[k + 1] = rk4_step(x_abs[k], US + u_dev[k], dt, params, substeps=20)
        y_dev_clean[k + 1] = x_abs[k + 1] - XS

    noise_std = noise_scale * np.array([4.0e-4, 4.0e-2, 4.0e-4], dtype=float)
    y_dev_noisy = y_dev_clean + rng.normal(0.0, noise_std, size=y_dev_clean.shape)

    return {
        "u_dev": u_dev,
        "x_abs": x_abs,
        "y_dev_clean": y_dev_clean,
        "y_dev_noisy": y_dev_noisy,
        "noise_std": noise_std,
        "time": np.arange(n_samples + 1, dtype=float) * dt,
        "tc_amp": np.array([tc_amp]),
        "f_amp": np.array([f_amp]),
    }


def identify_measured_state_ls(y_dev: Array, u_dev: Array, *, ridge: float = 1.0e-9) -> tuple[Array, Array]:
    """Fit x(k+1) = A x(k) + B u(k) by ridge-regularized least squares."""

    xk = np.asarray(y_dev[:-1], dtype=float)
    xkp1 = np.asarray(y_dev[1:], dtype=float)
    uk = np.asarray(u_dev, dtype=float)
    phi = np.hstack([xk, uk])
    gram = phi.T @ phi + ridge * np.eye(phi.shape[1])
    theta = np.linalg.solve(gram, phi.T @ xkp1)
    return theta[:3, :].T, theta[3:, :].T


def local_finite_difference_model(dt: float, params: CSTRParams, *, eps_x: Array | None = None, eps_u: Array | None = None) -> tuple[Array, Array]:
    """Compute a local discrete model by central differences of one-sample flow map."""

    eps_x = np.array([1.0e-4, 1.0e-2, 1.0e-4], dtype=float) if eps_x is None else np.asarray(eps_x, dtype=float)
    eps_u = np.array([1.0e-2, 1.0e-5], dtype=float) if eps_u is None else np.asarray(eps_u, dtype=float)

    A = np.zeros((3, 3), dtype=float)
    B = np.zeros((3, 2), dtype=float)
    for i in range(3):
        dx = np.zeros(3, dtype=float)
        dx[i] = eps_x[i]
        xp = rk4_step(XS + dx, US, dt, params, substeps=30) - XS
        xm = rk4_step(XS - dx, US, dt, params, substeps=30) - XS
        A[:, i] = (xp - xm) / (2.0 * eps_x[i])
    for j in range(2):
        du = np.zeros(2, dtype=float)
        du[j] = eps_u[j]
        xp = rk4_step(XS, US + du, dt, params, substeps=30) - XS
        xm = rk4_step(XS, US - du, dt, params, substeps=30) - XS
        B[:, j] = (xp - xm) / (2.0 * eps_u[j])
    return project_level_integrator(A, B, dt, params)


def project_level_integrator(A: Array, B: Array, dt: float, params: CSTRParams) -> tuple[Array, Array]:
    """Enforce the exact level relation h+ = h - dt/area * F_dev at nominal F0."""

    Ap = np.asarray(A, dtype=float).copy()
    Bp = np.asarray(B, dtype=float).copy()
    area = np.pi * params.r**2
    Ap[2, :] = np.array([0.0, 0.0, 1.0])
    Bp[2, :] = np.array([0.0, -dt / area])
    return Ap, Bp


def identify_regularized_noise_aware(
    y_dev_noisy: Array,
    u_dev: Array,
    A_prior: Array,
    B_prior: Array,
    dt: float,
    params: CSTRParams,
    *,
    noise_std: Array,
    prior_strength: float = 2.5e-2,
) -> tuple[Array, Array]:
    """Fit noisy PRBS data while regularizing toward a local perturbation model."""

    xk = np.asarray(y_dev_noisy[:-1], dtype=float)
    xkp1 = np.asarray(y_dev_noisy[1:], dtype=float)
    uk = np.asarray(u_dev, dtype=float)
    phi = np.hstack([xk, uk])

    theta_prior = np.vstack([A_prior.T, B_prior.T])
    theta = np.zeros((5, 3), dtype=float)

    # Output-wise weighting keeps temperature units from numerically dominating.
    for j in range(3):
        w = 1.0 / max(float(noise_std[j]), 1.0e-12)
        gram = (w * phi).T @ (w * phi) + prior_strength * np.eye(5)
        rhs = (w * phi).T @ (w * xkp1[:, j]) + prior_strength * theta_prior[:, j]
        theta[:, j] = np.linalg.solve(gram, rhs)

    A = theta[:3, :].T
    B = theta[3:, :].T
    return project_level_integrator(A, B, dt, params)


def simulate_discrete_model(A: Array, B: Array, u_dev: Array, x0_dev: Array | None = None) -> Array:
    """Simulate a discrete deviation model."""

    n = u_dev.shape[0]
    x = np.zeros((n + 1, A.shape[0]), dtype=float)
    if x0_dev is not None:
        x[0] = np.asarray(x0_dev, dtype=float)
    for k in range(n):
        x[k + 1] = A @ x[k] + B @ u_dev[k]
    return x


def step_test_models(models: dict[str, tuple[Array, Array]], dt: float, params: CSTRParams) -> dict[str, Array]:
    """Step-test nonlinear plant, textbook model, and identified models."""

    n_steps = 45
    cases = {
        "Tc +1 K": np.array([1.0, 0.0], dtype=float),
        "F +0.0002 m3/min": np.array([0.0, 0.0002], dtype=float),
    }
    out: dict[str, Array] = {"time": np.arange(n_steps + 1, dtype=float) * dt}

    for label, step in cases.items():
        u = np.repeat(step.reshape(1, 2), n_steps, axis=0)
        nonlinear = np.zeros((n_steps + 1, 3), dtype=float)
        x_abs = XS.copy()
        for k in range(n_steps):
            x_abs = rk4_step(x_abs, US + step, dt, params, substeps=30)
            nonlinear[k + 1] = x_abs - XS
        out[f"{label} nonlinear"] = nonlinear
        for name, (A, B) in models.items():
            out[f"{label} {name}"] = simulate_discrete_model(A, B, u)
    return out


def block_diag(blocks: Iterable[Array]) -> Array:
    blocks = list(blocks)
    rows = sum(b.shape[0] for b in blocks)
    cols = sum(b.shape[1] for b in blocks)
    out = np.zeros((rows, cols), dtype=float)
    r = c = 0
    for b in blocks:
        rr, cc = b.shape
        out[r:r + rr, c:c + cc] = b
        r += rr
        c += cc
    return out


def prediction_matrices(A: Array, B: Array, horizon: int) -> tuple[Array, Array]:
    nx, nu = B.shape
    sx = np.zeros((horizon * nx, nx), dtype=float)
    su = np.zeros((horizon * nx, horizon * nu), dtype=float)
    powers = [np.eye(nx)]
    for i in range(1, horizon + 1):
        powers.append(powers[-1] @ A)
    for i in range(1, horizon + 1):
        sx[(i - 1) * nx:i * nx] = powers[i]
        for j in range(i):
            su[(i - 1) * nx:i * nx, j * nu:(j + 1) * nu] = powers[i - 1 - j] @ B
    return sx, su


def unconstrained_mpc_first_move(A: Array, B: Array, e0: Array, horizon: int, Q: Array, R: Array, P: Array) -> Array:
    """Solve unconstrained finite-horizon regulation about the current target."""

    nx, nu = B.shape
    sx, su = prediction_matrices(A, B, horizon)
    qbar = block_diag([Q for _ in range(horizon - 1)] + [P])
    rbar = block_diag([R for _ in range(horizon)])
    hess = su.T @ qbar @ su + rbar
    grad = su.T @ qbar @ (sx @ e0)
    u_stack = -np.linalg.solve(hess + 1.0e-10 * np.eye(hess.shape[0]), grad)
    return u_stack[:nu]


def steady_target(
    A: Array,
    B: Array,
    Bd: Array,
    C: Array,
    Cd: Array,
    d_hat: Array,
    controlled_indices: list[int],
    r_sp: Array,
    u_sp: Array,
) -> tuple[Array, Array, Array, float]:
    """Compute a steady target, prioritizing exact c/h target equations."""

    nx, nu = B.shape
    H = np.zeros((len(controlled_indices), C.shape[0]), dtype=float)
    for row, idx in enumerate(controlled_indices):
        H[row, idx] = 1.0

    M = np.block([[np.eye(nx) - A, -B], [H @ C, np.zeros((len(controlled_indices), nu))]])
    rhs = np.concatenate([Bd @ d_hat, r_sp - H @ Cd @ d_hat])

    z0 = np.linalg.lstsq(M, rhs, rcond=None)[0]
    residual = float(np.linalg.norm(M @ z0 - rhs))

    _, s, vt = np.linalg.svd(M)
    rank = int(np.sum(s > 1.0e-9))
    Z = vt[rank:].T
    if Z.size:
        Eu = np.hstack([np.zeros((nu, nx)), np.eye(nu)])
        alpha = np.linalg.lstsq(Eu @ Z, u_sp - Eu @ z0, rcond=None)[0]
        z = z0 + Z @ alpha
    else:
        z = z0

    x_s = z[:nx]
    u_s = z[nx:]
    y_s = C @ x_s + Cd @ d_hat
    return x_s, u_s, y_s, residual


def kalman_update(xhat: Array, P: Array, y: Array, C: Array, R: Array) -> tuple[Array, Array, Array]:
    S = C @ P @ C.T + R
    K = P @ C.T @ np.linalg.pinv(S)
    innovation = y - C @ xhat
    I = np.eye(P.shape[0])
    xhat_new = xhat + K @ innovation
    P_new = (I - K @ C) @ P @ (I - K @ C).T + K @ R @ K.T
    return xhat_new, P_new, innovation


def terminal_penalty(A: Array, B: Array, Q: Array, R: Array) -> Array:
    try:
        return solve_discrete_are(A, B, Q + 1.0e-9 * np.eye(Q.shape[0]), R)
    except LinAlgError:
        return 10.0 * Q + np.eye(Q.shape[0])


def simulate_offset_free_mpc(
    A: Array,
    B: Array,
    dt: float,
    params: CSTRParams,
    *,
    n_steps: int = 100,
    disturbance_time: float = 10.0,
    inlet_flow_multiplier: float = 1.10,
) -> dict[str, Array]:
    """Closed-loop nonlinear CSTR simulation using an identified model in MPC."""

    nx, nu, nd, ny = 3, 2, 3, 3
    C = np.eye(3)

    # Disturbance model: output disturbance on c, output disturbance on h,
    # and an input-equivalent disturbance through the outlet-flow channel.
    Cd = np.array([[1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=float)
    Bd = np.column_stack([np.zeros(nx), np.zeros(nx), B[:, 1]])
    Ae = np.block([[A, Bd], [np.zeros((nd, nx)), np.eye(nd)]])
    Be = np.vstack([B, np.zeros((nd, nu))])
    Ce = np.hstack([C, Cd])

    # Bias the estimator to explain the inlet-flow step primarily through the
    # input-equivalent disturbance d3, not through the h sensor-bias disturbance.
    Qe = np.diag([1.0e-10, 1.0e-8, 1.0e-10, 1.0e-8, 1.0e-10, 1.0e-4])
    Re = np.diag([1.0e-8, 1.0e-6, 1.0e-8])
    Pcov = np.diag([1.0e-4, 1.0e-1, 1.0e-4, 1.0, 1.0e-2, 1.0])
    xhat_e = np.zeros(nx + nd, dtype=float)

    Qx = np.diag([8.0, 0.05, 8.0])
    R = np.diag([0.08, 0.08])
    Pterm = terminal_penalty(A, B, Qx, R)
    horizon = 14

    x_abs = np.zeros((n_steps + 1, nx), dtype=float)
    y_abs = np.zeros((n_steps + 1, ny), dtype=float)
    y_dev = np.zeros((n_steps + 1, ny), dtype=float)
    xhat = np.zeros((n_steps + 1, nx), dtype=float)
    dhat = np.zeros((n_steps + 1, nd), dtype=float)
    u_dev = np.zeros((n_steps, nu), dtype=float)
    u_abs = np.zeros((n_steps, nu), dtype=float)
    target_x = np.zeros((n_steps, nx), dtype=float)
    target_u = np.zeros((n_steps, nu), dtype=float)
    target_residual = np.zeros(n_steps, dtype=float)
    innovation = np.zeros((n_steps + 1, ny), dtype=float)

    x_abs[0] = XS.copy()
    y_abs[0] = x_abs[0]
    y_dev[0] = y_abs[0] - XS
    controlled = [0, 2]
    r_sp = np.array([0.0, 0.0], dtype=float)

    for k in range(n_steps):
        meas = x_abs[k] - XS
        xhat_e, Pcov, innov = kalman_update(xhat_e, Pcov, meas, Ce, Re)
        xhat[k] = xhat_e[:nx]
        dhat[k] = xhat_e[nx:]
        innovation[k] = innov

        xs_dev, us_dev, _ys_dev, res = steady_target(A, B, Bd, C, Cd, dhat[k], controlled, r_sp, np.zeros(nu))
        target_x[k] = xs_dev
        target_u[k] = us_dev
        target_residual[k] = res

        du = unconstrained_mpc_first_move(A, B, xhat[k] - xs_dev, horizon, Qx, R, Pterm)
        u_dev[k] = us_dev + du

        # Keep the nonlinear plant in a sensible local operating region.
        u_dev[k, 0] = float(np.clip(u_dev[k, 0], -15.0, 15.0))
        u_dev[k, 1] = float(np.clip(u_dev[k, 1], -0.04, 0.04))
        u_abs[k] = US + u_dev[k]

        F0_plant = params.F0 * (inlet_flow_multiplier if (k * dt) >= disturbance_time else 1.0)
        x_abs[k + 1] = rk4_step(x_abs[k], u_abs[k], dt, params, F0=F0_plant, substeps=30)
        y_abs[k + 1] = x_abs[k + 1]
        y_dev[k + 1] = y_abs[k + 1] - XS

        xhat_e = Ae @ xhat_e + Be @ u_dev[k]
        Pcov = Ae @ Pcov @ Ae.T + Qe

    xhat_e, Pcov, innov = kalman_update(xhat_e, Pcov, y_dev[-1], Ce, Re)
    xhat[-1] = xhat_e[:nx]
    dhat[-1] = xhat_e[nx:]
    innovation[-1] = innov

    rank_mat = np.block([[np.eye(nx) - A, Bd], [C, Cd]])

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
        "target_residual": target_residual,
        "innovation": innovation,
        "augmented_rank": np.array([np.linalg.matrix_rank(rank_mat)], dtype=float),
        "augmented_rank_required": np.array([nx + nd], dtype=float),
    }


def rmse(a: Array, b: Array) -> Array:
    return np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2, axis=0))


def spectral_radius(A: Array) -> float:
    return float(np.max(np.abs(np.linalg.eigvals(A))))


def model_metrics(name: str, A: Array, B: Array, data: dict[str, Array], steps: dict[str, Array]) -> dict[str, object]:
    replay = simulate_discrete_model(A, B, data["u_dev"])
    metrics: dict[str, object] = {
        "name": name,
        "A": A,
        "B": B,
        "eigenvalues": np.linalg.eigvals(A),
        "spectral_radius": spectral_radius(A),
        "open_loop_replay_rmse_vs_clean": rmse(replay, data["y_dev_clean"]),
        "A_error_vs_textbook_fro": float(np.linalg.norm(A - A_TEXTBOOK)),
        "B_error_vs_textbook_fro": float(np.linalg.norm(B - B_TEXTBOOK)),
    }
    for case in ["Tc +1 K", "F +0.0002 m3/min"]:
        metrics[f"{case} rmse_vs_nonlinear"] = rmse(steps[f"{case} {name}"], steps[f"{case} nonlinear"])
    return metrics


def write_csv(path: Path, header: list[str], rows: Array) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(np.asarray(rows, dtype=float).tolist())


def save_json(path: Path, payload: dict) -> None:
    def convert(obj):
        if isinstance(obj, np.ndarray):
            if np.iscomplexobj(obj):
                if obj.ndim == 1:
                    return [{"real": float(np.real(v)), "imag": float(np.imag(v))} for v in obj]
                return [[{"real": float(np.real(v)), "imag": float(np.imag(v))} for v in row] for row in obj]
            return obj.tolist()
        if isinstance(obj, (np.floating, np.integer)):
            return obj.item()
        if isinstance(obj, (complex, np.complexfloating)):
            return {"real": float(np.real(obj)), "imag": float(np.imag(obj))}
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, dict):
            return {str(k): convert(v) for k, v in obj.items()}
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
    y_clean = data["y_dev_clean"]
    y_noisy = data["y_dev_noisy"]
    fig, axes = plt.subplots(5, 1, figsize=(11, 10), sharex=True)
    axes[0].step(t[:-1], u[:, 0], where="post")
    axes[0].set_ylabel(INPUT_NAMES[0])
    axes[1].step(t[:-1], u[:, 1], where="post")
    axes[1].set_ylabel(INPUT_NAMES[1])
    for i, name in enumerate(STATE_NAMES):
        axes[i + 2].plot(t, y_clean[:, i], label="clean nonlinear")
        axes[i + 2].plot(t, y_noisy[:, i], label="noisy measurement", alpha=0.55)
        axes[i + 2].set_ylabel(name)
        axes[i + 2].legend(fontsize=8)
    axes[-1].set_xlabel("time [min]")
    for ax in axes:
        ax.grid(True, alpha=0.3)
    fig.suptitle("Exercise 1.63 PRBS identification dataset")
    fig.tight_layout()
    path = out_dir / "identification_data.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def plot_model_replay(out_dir: Path, data: dict[str, Array], models: dict[str, tuple[Array, Array]]) -> Path:
    t = data["time"]
    fig, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
    for i, name in enumerate(STATE_NAMES):
        axes[i].plot(t, data["y_dev_clean"][:, i], label="clean nonlinear", linewidth=2.0)
        axes[i].plot(t, data["y_dev_noisy"][:, i], label="noisy measurement", alpha=0.25)
        for model_name, (A, B) in models.items():
            y_model = simulate_discrete_model(A, B, data["u_dev"])
            axes[i].plot(t, y_model[:, i], label=model_name, linestyle="--" if model_name == "textbook" else None)
        axes[i].set_ylabel(name)
        axes[i].grid(True, alpha=0.3)
        axes[i].legend(fontsize=7, ncol=2)
    axes[-1].set_xlabel("time [min]")
    fig.suptitle("Open-loop replay: why raw noisy LS was misleading")
    fig.tight_layout()
    path = out_dir / "identification_fit_comparison.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def plot_step_tests(out_dir: Path, steps: dict[str, Array], model_names: list[str]) -> Path:
    t = steps["time"]
    cases = ["Tc +1 K", "F +0.0002 m3/min"]
    fig, axes = plt.subplots(3, 2, figsize=(13, 8), sharex=True)
    for col, case in enumerate(cases):
        for row, state_name in enumerate(STATE_NAMES):
            ax = axes[row, col]
            ax.plot(t, steps[f"{case} nonlinear"][:, row], label="nonlinear plant", linewidth=2.0)
            for model_name in model_names:
                ax.plot(t, steps[f"{case} {model_name}"][:, row], label=model_name)
            ax.set_title(case if row == 0 else "")
            ax.set_ylabel(state_name)
            ax.grid(True, alpha=0.3)
            if row == 0:
                ax.legend(fontsize=7)
    axes[-1, 0].set_xlabel("time [min]")
    axes[-1, 1].set_xlabel("time [min]")
    fig.suptitle("Step-test comparison")
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
    for i, label in enumerate(ABS_STATE_NAMES):
        axes[i].plot(t, x[:, i])
        axes[i].axhline(XS[i], linestyle="--", linewidth=1.0, label="nominal")
        axes[i].axvline(10.0, linestyle=":", linewidth=1.2, label="+10% F0 step" if i == 0 else None)
        axes[i].set_ylabel(label)
        axes[i].grid(True, alpha=0.3)
        axes[i].legend(fontsize=8)
    axes[-1].set_xlabel("time [min]")
    fig.suptitle("Closed-loop nonlinear CSTR: selected identified model + offset-free MPC")
    fig.tight_layout()
    path_y = out_dir / "closed_loop_outputs.png"
    fig.savefig(path_y, dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
    for i, label in enumerate(ABS_INPUT_NAMES):
        axes[i].step(tu, u[:, i], where="post")
        axes[i].axhline(US[i], linestyle="--", linewidth=1.0)
        axes[i].axvline(10.0, linestyle=":", linewidth=1.2)
        axes[i].set_ylabel(label)
        axes[i].grid(True, alpha=0.3)
    axes[-1].set_xlabel("time [min]")
    fig.suptitle("Manipulated inputs")
    fig.tight_layout()
    path_u = out_dir / "closed_loop_inputs.png"
    fig.savefig(path_u, dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(3, 1, figsize=(11, 7), sharex=True)
    labels = ["d1: c output bias", "d2: h output bias", "d3: F-channel input disturbance"]
    for i, label in enumerate(labels):
        axes[i].plot(t, d[:, i])
        axes[i].axvline(10.0, linestyle=":", linewidth=1.2)
        axes[i].set_ylabel(label)
        axes[i].grid(True, alpha=0.3)
    axes[-1].set_xlabel("time [min]")
    fig.suptitle("Estimated integrating disturbances")
    fig.tight_layout()
    path_d = out_dir / "closed_loop_disturbances.png"
    fig.savefig(path_d, dpi=160)
    plt.close(fig)
    return path_y, path_u, path_d


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Exercise 1.63 nonlinear CSTR system-identification sandbox")
    parser.add_argument("--out", default=None, help="Output directory. Default: ./out/ex_1_63 beside this script")
    parser.add_argument("--samples", type=int, default=700, help="PRBS identification samples")
    parser.add_argument("--dt", type=float, default=1.0, help="Sample time [min]")
    parser.add_argument("--seed", type=int, default=163, help="Random seed")
    parser.add_argument("--tc-amp", type=float, default=0.20, help="PRBS amplitude for coolant temperature deviation [K]")
    parser.add_argument("--f-amp", type=float, default=0.00020, help="PRBS amplitude for outlet flow deviation [m3/min]")
    parser.add_argument("--noise-scale", type=float, default=1.0, help="Multiplier on default measurement noise standard deviations")
    parser.add_argument("--closed-loop-steps", type=int, default=100, help="Closed-loop simulation length in samples")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    script_dir = Path(__file__).resolve().parent
    out_dir = Path(args.out).expanduser().resolve() if args.out else script_dir / "out" / "ex_1_63"
    out_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(args.seed)
    params = CSTRParams()

    data = make_identification_data(
        args.samples,
        args.dt,
        rng,
        params,
        tc_amp=args.tc_amp,
        f_amp=args.f_amp,
        noise_scale=args.noise_scale,
    )

    A_raw, B_raw = identify_measured_state_ls(data["y_dev_noisy"], data["u_dev"])
    A_clean, B_clean = identify_measured_state_ls(data["y_dev_clean"], data["u_dev"])
    A_clean, B_clean = project_level_integrator(A_clean, B_clean, args.dt, params)
    A_fd, B_fd = local_finite_difference_model(args.dt, params)
    A_selected, B_selected = identify_regularized_noise_aware(
        data["y_dev_noisy"],
        data["u_dev"],
        A_fd,
        B_fd,
        args.dt,
        params,
        noise_std=data["noise_std"],
        prior_strength=2.5e-2,
    )

    models: dict[str, tuple[Array, Array]] = {
        "textbook": (A_TEXTBOOK, B_TEXTBOOK),
        "raw_noisy_ls": (A_raw, B_raw),
        "clean_replay_ls": (A_clean, B_clean),
        "local_finite_difference": (A_fd, B_fd),
        "regularized_noise_aware": (A_selected, B_selected),
    }

    steps = step_test_models(models, args.dt, params)
    metrics = {name: model_metrics(name, A, B, data, steps) for name, (A, B) in models.items()}
    cl = simulate_offset_free_mpc(A_selected, B_selected, args.dt, params, n_steps=args.closed_loop_steps)

    plots: dict[str, Path] = {}
    plots["identification_data"] = plot_identification_data(out_dir, data)
    plots["identification_fit_comparison"] = plot_model_replay(out_dir, data, models)
    plots["step_test_comparison"] = plot_step_tests(out_dir, steps, list(models.keys()))
    py, pu, pd = plot_closed_loop(out_dir, cl)
    plots["closed_loop_outputs"] = py
    plots["closed_loop_inputs"] = pu
    plots["closed_loop_disturbances"] = pd

    rows = np.column_stack([
        data["time"],
        data["y_dev_clean"],
        data["y_dev_noisy"],
        np.vstack([data["u_dev"], [np.nan, np.nan]]),
    ])
    write_csv(
        out_dir / "identification_dataset.csv",
        ["time", "c_clean_dev", "T_clean_dev", "h_clean_dev", "c_noisy_dev", "T_noisy_dev", "h_noisy_dev", "Tc_dev", "F_dev"],
        rows,
    )
    write_csv(
        out_dir / "closed_loop_outputs.csv",
        ["time", "c", "T", "h", "c_dev", "T_dev", "h_dev", "xhat_c_dev", "xhat_T_dev", "xhat_h_dev", "d1", "d2", "d3"],
        np.column_stack([cl["time"], cl["x_abs"], cl["y_dev"], cl["xhat"], cl["dhat"]]),
    )
    write_csv(
        out_dir / "closed_loop_inputs.csv",
        ["time", "Tc", "F", "Tc_dev", "F_dev", "target_Tc_dev", "target_F_dev"],
        np.column_stack([cl["time_u"], cl["u_abs"], cl["u_dev"], cl["target_u"]]),
    )

    final_offsets = cl["x_abs"][-1] - XS
    result = {
        "title": "Exercise 1.63 - System identification of nonlinear CSTR",
        "sample_time_min": args.dt,
        "identification_samples": args.samples,
        "seed": args.seed,
        "prbs_amplitudes": {"Tc_dev_K": args.tc_amp, "F_dev_m3_min": args.f_amp},
        "measurement_noise_std": data["noise_std"],
        "nominal_state_XS": XS,
        "nominal_input_US": US,
        "params": asdict(params),
        "models": metrics,
        "selected_model_name": "regularized_noise_aware",
        "selected_A": A_selected,
        "selected_B": B_selected,
        "raw_noisy_A": A_raw,
        "raw_noisy_B": B_raw,
        "local_finite_difference_A": A_fd,
        "local_finite_difference_B": B_fd,
        "textbook_A": A_TEXTBOOK,
        "textbook_B": B_TEXTBOOK,
        "closed_loop": {
            "disturbance": "+10% inlet flowrate F0 at t = 10 min",
            "final_offsets_absolute_minus_nominal": final_offsets,
            "final_controlled_offsets_c_and_h": final_offsets[[0, 2]],
            "final_input_deviation": cl["u_dev"][-1],
            "final_disturbance_estimate": cl["dhat"][-1],
            "augmented_rank_required": cl["augmented_rank_required"],
            "augmented_rank_observed": cl["augmented_rank"],
        },
        "plots": {k: str(v) for k, v in plots.items()},
        "what_went_wrong_in_previous_script": {
            "errors_in_variables": "The old raw_noisy_ls model regressed noisy y(k+1) on noisy y(k). That biases A because measurement noise is inside the regressor, not just the residual.",
            "weak_excitation": "The PRBS amplitudes are intentionally small to avoid nonlinear CSTR ignition, so the signal-to-noise ratio is poor, especially for temperature.",
            "level_integrator_corruption": "The old fit allowed noisy c and T measurements to leak into the level row. The true level dynamics are an integrator driven by inlet minus outlet flow.",
            "control_consequence": "The corrupted identified model can pass a short replay plot but produce the wrong target/input behavior in the offset-free MPC closed-loop simulation.",
        },
    }
    save_json(out_dir / "ex_1_63_results.json", result)

    with (out_dir / "calculation_log.txt").open("w", encoding="utf-8") as f:
        f.write("Rawlings/Mayne/Diehl MPC - Exercise 1.63 upgraded sandbox\n")
        f.write("System identification of the nonlinear CSTR from Example 1.11\n\n")
        f.write(f"Output directory: {out_dir}\n")
        f.write(f"Sample time: {args.dt} min\n")
        f.write(f"Identification samples: {args.samples}\n")
        f.write(f"Random seed: {args.seed}\n")
        f.write(f"PRBS amplitudes: Tc={args.tc_amp} K, F={args.f_amp} m3/min\n")
        f.write(f"Measurement noise std: {data['noise_std']}\n\n")

        f.write("What went wrong before\n")
        f.write("  1. The old script used ordinary least squares on noisy measured states.\n")
        f.write("  2. That is an errors-in-variables problem; the noise enters y(k), the regressor.\n")
        f.write("  3. The deliberately small PRBS amplitudes keep the plant local but reduce SNR.\n")
        f.write("  4. The level row should be an exact integrator, but noisy LS invented false c/T coupling.\n")
        f.write("  5. A replay plot can look acceptable while the closed-loop target calculation is wrong.\n\n")

        for name, m in metrics.items():
            f.write(f"Model: {name}\n")
            f.write("A matrix\n")
            f.write(np.array2string(np.asarray(m["A"]), precision=7) + "\n")
            f.write("B matrix\n")
            f.write(np.array2string(np.asarray(m["B"]), precision=7) + "\n")
            f.write(f"eigenvalues: {m['eigenvalues']}\n")
            f.write(f"spectral radius: {m['spectral_radius']}\n")
            f.write(f"A error vs textbook Frobenius: {m['A_error_vs_textbook_fro']}\n")
            f.write(f"B error vs textbook Frobenius: {m['B_error_vs_textbook_fro']}\n")
            f.write(f"open-loop replay RMSE vs clean [c,T,h]: {m['open_loop_replay_rmse_vs_clean']}\n")
            f.write(f"Tc step RMSE vs nonlinear [c,T,h]: {m['Tc +1 K rmse_vs_nonlinear']}\n")
            f.write(f"F step RMSE vs nonlinear [c,T,h]: {m['F +0.0002 m3/min rmse_vs_nonlinear']}\n\n")

        f.write("Selected model for closed-loop MPC: regularized_noise_aware\n")
        f.write("Offset-free MPC closed-loop test\n")
        f.write("  disturbance: +10% inlet flowrate F0 at t = 10 min\n")
        f.write(f"  augmented detectability rank observed: {cl['augmented_rank'][0]:.0f} / {cl['augmented_rank_required'][0]:.0f}\n")
        f.write(f"  final output offsets [c-cs, T-Ts, h-hs]: {final_offsets}\n")
        f.write(f"  final controlled-variable offsets [c-cs, h-hs]: {final_offsets[[0, 2]]}\n")
        f.write(f"  final input deviation [Tc-Tcs, F-Fs]: {cl['u_dev'][-1]}\n")
        f.write(f"  final disturbance estimate [d1,d2,d3]: {cl['dhat'][-1]}\n\n")

        f.write("Files written\n")
        for name, path in plots.items():
            f.write(f"  {name}: {path}\n")
        f.write("  ex_1_63_results.json\n")
        f.write("  identification_dataset.csv\n")
        f.write("  closed_loop_outputs.csv\n")
        f.write("  closed_loop_inputs.csv\n")

    print(f"Done. Wrote Exercise 1.63 upgraded outputs to: {out_dir}")
    print(f"Script: {Path(__file__).resolve()}")
    print("Selected identified A:")
    print(A_selected)
    print("Selected identified B:")
    print(B_selected)
    print(f"Final controlled offsets [c, h]: {final_offsets[[0, 2]]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
