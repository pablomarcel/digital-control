#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
example_1_11.py

Rawlings / Mayne / Diehl, Model Predictive Control, Example 1.11 sandbox.

Focus:
    More measured outputs than inputs and zero offset.

The script implements an educational reproduction of parts (a), (b), and (c):

    (a) two integrating output disturbances on the two controlled variables
        c and h. This violates the Lemma 1.10 prescription nd = p because
        there are p = 3 measurements. The simulation should settle with offset.

    (b) three integrating output disturbances, one on each measured output.
        This follows nd = p, but the augmented system is not detectable because
        the tank level h is already an integrator.

    (c) three integrating disturbances: output disturbances on c and h, plus
        an input-like disturbance through the outlet-flow column of B. This
        augmented system is detectable. The simulation should remove offset in
        c and h and push the remaining disturbance effect mainly into T.

The controller is a transparent offset-free linear controller using:
    - the linearized discrete-time reactor model from Example 1.11,
    - a steady-state Kalman estimator for the augmented [x; d] model,
    - a disturbance-aware steady-state target selector,
    - an unconstrained infinite-horizon LQR regulator in deviation variables,
    - nonlinear continuous-time reactor dynamics for the plant simulation.

Outputs are written to out/example_1_11 relative to this script location.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import csv
import json
import math
import textwrap

import numpy as np
from numpy.linalg import matrix_rank, norm, cond, eigvals
from scipy.integrate import solve_ivp
from scipy.linalg import solve_discrete_are, block_diag
import matplotlib.pyplot as plt


# --------------------------------------------------------------------------------------
# Paths and small helpers
# --------------------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = SCRIPT_DIR / "out" / "example_1_11"


def arrs(value: Any) -> Any:
    """Convert NumPy objects to JSON-safe objects."""
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    if isinstance(value, list):
        return [arrs(v) for v in value]
    if isinstance(value, tuple):
        return [arrs(v) for v in value]
    if isinstance(value, dict):
        return {str(k): arrs(v) for k, v in value.items()}
    return value


def fmt(x: Any, precision: int = 8) -> str:
    """Compact numeric array formatting for logs."""
    return np.array2string(np.asarray(x), precision=precision, suppress_small=False)


def write_csv(path: Path, headers: list[str], rows: list[list[Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


# --------------------------------------------------------------------------------------
# Example 1.11 reactor model data
# --------------------------------------------------------------------------------------

@dataclass(frozen=True)
class ReactorNominal:
    F0: float = 0.1          # m^3/min
    T0: float = 350.0        # K
    c0: float = 1.0          # kmol/m^3
    r: float = 0.219         # m
    k0: float = 7.2e10       # 1/min
    E_over_R: float = 8750.0 # K
    U: float = 54.94         # kJ/(min m^2 K)
    rho: float = 1000.0      # kg/m^3
    Cp: float = 0.239        # kJ/(kg K)
    dH: float = -5.0e4       # kJ/kmol
    cs: float = 0.878        # kmol/m^3
    Ts: float = 324.5        # K
    hs: float = 0.659        # m
    Tcs: float = 300.0       # K
    Fs: float = 0.1          # m^3/min

    @property
    def area(self) -> float:
        return math.pi * self.r**2


NOM = ReactorNominal()

# Linearized discrete model from the book. Variables are deviations from nominal.
A = np.array([
    [0.2681, -0.00338, -0.00728],
    [9.703,   0.3279,  -25.44],
    [0.0,     0.0,      1.0],
], dtype=float)
B = np.array([
    [-0.00537,  0.1655],
    [ 1.297,   97.91],
    [ 0.0,     -6.637],
], dtype=float)
Bp_true = np.array([[-0.1175], [69.74], [6.637]], dtype=float)
C = np.eye(3)
H = np.array([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])  # controlled variables are c and h

STATE_NAMES = ["c", "T", "h"]
OUTPUT_NAMES = ["c", "T", "h"]
INPUT_NAMES = ["Tc", "F"]
CONTROLLED_NAMES = ["c", "h"]

X_NOM = np.array([NOM.cs, NOM.Ts, NOM.hs], dtype=float)
U_NOM = np.array([NOM.Tcs, NOM.Fs], dtype=float)
Y_SP_DEV = np.zeros(3)
R_SP_DEV = np.zeros(2)
U_SP_DEV = np.zeros(2)


# --------------------------------------------------------------------------------------
# Nonlinear reactor plant
# --------------------------------------------------------------------------------------

def reaction_rate(c: float, T: float, p: ReactorNominal = NOM) -> float:
    return p.k0 * math.exp(-p.E_over_R / T) * c


def reactor_rhs(_t: float, x_abs: np.ndarray, u_abs: np.ndarray, F0_actual: float, p: ReactorNominal = NOM) -> np.ndarray:
    c, T, h = map(float, x_abs)
    Tc, F = map(float, u_abs)
    h_safe = max(h, 0.05)
    area = p.area
    rate = reaction_rate(c, T, p)
    dc = F0_actual * (p.c0 - c) / (area * h_safe) - rate
    dT = (
        F0_actual * (p.T0 - T) / (area * h_safe)
        + (-p.dH) / (p.rho * p.Cp) * rate
        + 2.0 * p.U / (p.r * p.rho * p.Cp) * (Tc - T)
    )
    dh = (F0_actual - F) / area
    return np.array([dc, dT, dh], dtype=float)


def integrate_reactor(x_abs: np.ndarray, u_abs: np.ndarray, F0_actual: float, dt: float = 1.0) -> np.ndarray:
    sol = solve_ivp(
        fun=lambda t, x: reactor_rhs(t, x, u_abs, F0_actual),
        t_span=(0.0, dt),
        y0=np.asarray(x_abs, dtype=float),
        method="RK45",
        rtol=1e-8,
        atol=1e-10,
        max_step=0.05,
    )
    if not sol.success:
        raise RuntimeError(sol.message)
    out = sol.y[:, -1]
    # Keep the educational simulation physically sane if aggressive tuning is tested.
    out[0] = max(out[0], 1e-6)
    out[1] = max(out[1], 250.0)
    out[2] = max(out[2], 0.05)
    return out


# --------------------------------------------------------------------------------------
# Linear control, target selection, detectability checks
# --------------------------------------------------------------------------------------

def lqr_gain(A_: np.ndarray, B_: np.ndarray, Q: np.ndarray, R: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    P = solve_discrete_are(A_, B_, Q, R)
    K = -np.linalg.solve(R + B_.T @ P @ B_, B_.T @ P @ A_)
    Acl = A_ + B_ @ K
    eig = eigvals(Acl)
    rho = float(max(abs(eig)))
    return K, P, eig, rho


def detectability_rank_matrix(A_: np.ndarray, C_: np.ndarray, Bd: np.ndarray, Cd: np.ndarray) -> np.ndarray:
    return np.block([[np.eye(A_.shape[0]) - A_, -Bd], [C_, Cd]])


def target_selector(
    d_hat: np.ndarray,
    Bd: np.ndarray,
    Cd: np.ndarray,
    Qs: np.ndarray,
    Rs: np.ndarray,
) -> dict[str, Any]:
    """Solve the unconstrained disturbance-aware target problem by KKT equations."""
    n = A.shape[0]
    m = B.shape[1]
    zdim = n + m
    d_hat = np.asarray(d_hat, dtype=float).reshape(-1)

    # Objective: 0.5||us - usp||_Rs^2 + 0.5||C xs + Cd d - ysp||_Qs^2
    G = np.zeros((zdim, zdim))
    g = np.zeros(zdim)
    G[:n, :n] = C.T @ Qs @ C
    G[n:, n:] = Rs
    g[:n] = C.T @ Qs @ (Cd @ d_hat - Y_SP_DEV)
    g[n:] = -Rs @ U_SP_DEV

    M = np.block([[np.eye(n) - A, -B], [H @ C, np.zeros((H.shape[0], m))]])
    b = np.concatenate([Bd @ d_hat, R_SP_DEV - H @ Cd @ d_hat])

    KKT = np.block([[G, M.T], [M, np.zeros((M.shape[0], M.shape[0]))]])
    rhs = np.concatenate([-g, b])
    sol = np.linalg.lstsq(KKT, rhs, rcond=None)[0]
    z = sol[:zdim]
    lam = sol[zdim:]
    xs = z[:n]
    us = z[n:]
    ys = C @ xs + Cd @ d_hat
    rs = H @ ys
    obj = 0.5 * float((us - U_SP_DEV).T @ Rs @ (us - U_SP_DEV)) + 0.5 * float((ys - Y_SP_DEV).T @ Qs @ (ys - Y_SP_DEV))
    eq = M @ z - b
    grad = G @ z + g + M.T @ lam
    return {
        "xs": xs,
        "us": us,
        "ys": ys,
        "rs": rs,
        "objective": obj,
        "M": M,
        "b": b,
        "equality_residual": eq,
        "kkt_residual": np.concatenate([grad, eq]),
        "kkt_condition": float(cond(KKT)),
        "rank_M": int(matrix_rank(M)),
        "rank_augmented": int(matrix_rank(np.column_stack([M, b]))),
    }


def steady_kalman_gain(A_aug: np.ndarray, C_aug: np.ndarray, Qe: np.ndarray, Re: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    # DARE for predictor covariance. Q/R are regularized in the caller.
    P = solve_discrete_are(A_aug.T, C_aug.T, Qe, Re)
    L = P @ C_aug.T @ np.linalg.inv(C_aug @ P @ C_aug.T + Re)
    Aerr = (np.eye(A_aug.shape[0]) - L @ C_aug) @ A_aug
    eig = eigvals(Aerr)
    rho = float(max(abs(eig)))
    return L, P, eig, rho


@dataclass
class DisturbanceDesign:
    name: str
    description: str
    Bd: np.ndarray
    Cd: np.ndarray
    simulate: bool
    textbook_expected: str
    Qd_diag: np.ndarray


def make_designs() -> list[DisturbanceDesign]:
    Bd_a = np.zeros((3, 2))
    Cd_a = np.array([[1.0, 0.0], [0.0, 0.0], [0.0, 1.0]])

    Bd_b = np.zeros((3, 3))
    # Textbook order places the third disturbance on T and the second on h.
    Cd_b = np.array([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, 1.0, 0.0]])

    Bd_c = np.array([[0.0, 0.0, 0.1655], [0.0, 0.0, 97.91], [0.0, 0.0, -6.637]])
    Cd_c = np.array([[1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0]])

    return [
        DisturbanceDesign(
            name="part_a_nd2_output_disturbances_on_c_and_h",
            description="Part (a): two integrating output disturbances on c and h only; nd=2 although p=3.",
            Bd=Bd_a,
            Cd=Cd_a,
            simulate=True,
            textbook_expected="Textbook Figures 1.8-1.9: c, T, and h all display nonzero steady offset.",
            Qd_diag=np.array([2e-3, 2e-3]),
        ),
        DisturbanceDesign(
            name="part_b_nd3_output_disturbances_on_all_outputs",
            description="Part (b): three integrating output disturbances. Rank fails because h is already an integrator.",
            Bd=Bd_b,
            Cd=Cd_b,
            simulate=False,
            textbook_expected="The augmented system is not detectable; rank is 5 instead of 6.",
            Qd_diag=np.array([2e-3, 2e-3, 2e-3]),
        ),
        DisturbanceDesign(
            name="part_c_nd3_output_c_h_plus_input_F_disturbance",
            description="Part (c): output disturbances on c and h plus an input-like disturbance through outlet flow F.",
            Bd=Bd_c,
            Cd=Cd_c,
            simulate=True,
            textbook_expected="Textbook Figures 1.10-1.11: zero offset in controlled variables c and h; disturbance effect mostly appears in T.",
            Qd_diag=np.array([2e-3, 2e-3, 5e-4]),
        ),
    ]


def simulate_design(design: DisturbanceDesign, log: list[str]) -> dict[str, Any]:
    steps = 50
    dt = 1.0
    step_time = 10
    F0_step = 1.10 * NOM.F0
    p_step_dev = F0_step - NOM.F0

    n = A.shape[0]
    m = B.shape[1]
    p = C.shape[0]
    nd = design.Cd.shape[1]

    A_aug = np.block([[A, design.Bd], [np.zeros((nd, n)), np.eye(nd)]])
    B_aug = np.vstack([B, np.zeros((nd, m))])
    C_aug = np.hstack([C, design.Cd])

    # Deterministic regulator. Penalize controlled variables strongly, T mildly.
    Q = np.diag([45.0, 0.008, 45.0])
    R = np.diag([0.0006, 45.0])
    K, P_lqr, eig_cl, rho_cl = lqr_gain(A, B, Q, R)

    # Target tuning. Controlled variables are enforced by equalities; y penalty helps choose T when possible.
    Qs = np.diag([35.0, 0.01, 35.0])
    Rs = np.diag([0.0005, 25.0])

    # Estimator tuning. The book states zero state-noise covariance except integrating states
    # and zero measurement-noise covariance. We regularize with tiny positive values for numerics.
    eps = 1e-9
    Qe = block_diag(np.eye(n) * eps, np.diag(design.Qd_diag))
    Re = np.eye(p) * 1e-7
    L, P_est, eig_est, rho_est = steady_kalman_gain(A_aug, C_aug, Qe, Re)

    zhat = np.zeros(n + nd)
    x_abs = X_NOM.copy()

    rows: list[list[Any]] = []
    hist = {
        "time": [], "x_abs": [], "x_dev": [], "y_abs": [], "y_dev": [],
        "u_abs": [], "u_dev": [], "dhat": [], "xs": [], "us": [], "ys": [], "rs": [],
        "controlled_error": [], "plant_disturbance_dev": [],
    }

    selected_rows = {0, 1, 2, 9, 10, 11, 15, 25, 45, 48, 49, 50}
    selected_log: list[str] = []

    for k in range(steps + 1):
        t = k * dt
        y_dev = x_abs - X_NOM
        y_abs = x_abs.copy()

        # Measurement update at current sample.
        innovation = y_dev - C_aug @ zhat
        zcorr = zhat + L @ innovation
        xhat = zcorr[:n]
        dhat = zcorr[n:]
        target = target_selector(dhat, design.Bd, design.Cd, Qs, Rs)
        xs = target["xs"]
        us = target["us"]
        ue = us + K @ (xhat - xs)
        u_dev = ue.copy()
        u_abs = U_NOM + u_dev
        # Avoid nonphysical extreme moves while preserving the textbook-like response.
        u_abs[0] = np.clip(u_abs[0], 285.0, 315.0)
        u_abs[1] = np.clip(u_abs[1], 0.05, 0.16)
        u_dev = u_abs - U_NOM

        r_abs = H @ y_abs
        r_sp_abs = H @ X_NOM
        c_err = float(y_abs[0] - NOM.cs)
        h_err = float(y_abs[2] - NOM.hs)
        controlled_error = np.array([c_err, h_err])

        hist["time"].append(t)
        hist["x_abs"].append(x_abs.copy())
        hist["x_dev"].append(y_dev.copy())
        hist["y_abs"].append(y_abs.copy())
        hist["y_dev"].append(y_dev.copy())
        hist["u_abs"].append(u_abs.copy() if k < steps else np.full(m, np.nan))
        hist["u_dev"].append(u_dev.copy() if k < steps else np.full(m, np.nan))
        hist["dhat"].append(dhat.copy())
        hist["xs"].append(xs.copy())
        hist["us"].append(us.copy())
        hist["ys"].append(target["ys"].copy())
        hist["rs"].append(target["rs"].copy())
        hist["controlled_error"].append(controlled_error.copy())
        hist["plant_disturbance_dev"].append(0.0 if k < step_time else p_step_dev)

        rows.append([
            k, t, *x_abs.tolist(), *y_dev.tolist(), *(u_abs.tolist() if k < steps else [math.nan, math.nan]),
            *dhat.tolist(), *xs.tolist(), *us.tolist(), c_err, h_err, float(norm(controlled_error))
        ])

        if k in selected_rows:
            selected_log.append(
                f"  k={k:2d}: y_abs=(c={y_abs[0]:.8g}, T={y_abs[1]:.8g}, h={y_abs[2]:.8g}), "
                f"u_abs=(Tc={u_abs[0]:.8g}, F={u_abs[1]:.8g}), "
                f"dhat={fmt(dhat, 5)}, c_err={c_err:.8g}, h_err={h_err:.8g}"
            )

        if k < steps:
            # Time update for next sample with applied input.
            zhat = A_aug @ zcorr + B_aug @ u_dev
            F0_actual = NOM.F0 if k < step_time - 1 else F0_step
            x_abs = integrate_reactor(x_abs, u_abs, F0_actual, dt=dt)

    for key in hist:
        hist[key] = np.asarray(hist[key], dtype=float)

    final_y = hist["y_abs"][-1]
    final_u = hist["u_abs"][-2]
    final_dhat = hist["dhat"][-1]
    final_c_offset = float(final_y[0] - NOM.cs)
    final_T_offset = float(final_y[1] - NOM.Ts)
    final_h_offset = float(final_y[2] - NOM.hs)
    final_controlled_norm = float(norm([final_c_offset, final_h_offset]))

    log.extend([
        "",
        "Simulation and controller setup",
        "  Nonlinear plant is integrated with solve_ivp at 1 min sample time.",
        "  Linear model variables are deviations from nominal steady state.",
        "  Controller structure: estimator -> target selector -> LQR deviation regulator.",
        "  Regulator Q =",
        fmt(Q),
        "  Regulator R =",
        fmt(R),
        "  LQR Riccati P =",
        fmt(P_lqr),
        "  K for u_dev = us + K*(xhat-xs) =",
        fmt(K),
        "  eig(A+B K) = " + fmt(eig_cl),
        f"  spectral radius(A+B K) = {rho_cl:.12g}",
        f"  regulator stable? {rho_cl < 1.0}",
        "",
        "Estimator design",
        "  A_aug =",
        fmt(A_aug),
        "  C_aug =",
        fmt(C_aug),
        "  Qe =",
        fmt(Qe),
        "  Re =",
        fmt(Re),
        "  steady estimator covariance P =",
        fmt(P_est),
        "  estimator gain L =",
        fmt(L),
        "  eig((I-LCaug)Aaug) = " + fmt(eig_est),
        f"  spectral radius = {rho_est:.12g}",
        f"  estimator stable? {rho_est < 1.0}",
        "",
        "Final simulation result",
        f"  final measured outputs: c={final_y[0]:.12g}, T={final_y[1]:.12g}, h={final_y[2]:.12g}",
        f"  final manipulated inputs: Tc={final_u[0]:.12g}, F={final_u[1]:.12g}",
        "  final d_hat = " + fmt(final_dhat),
        f"  final c offset from nominal = {final_c_offset:.12g}",
        f"  final T offset from nominal = {final_T_offset:.12g}",
        f"  final h offset from nominal = {final_h_offset:.12g}",
        f"  final controlled-variable offset norm sqrt(c_offset^2+h_offset^2) = {final_controlled_norm:.12g}",
        "",
        "Selected simulation rows",
        *selected_log,
    ])

    headers = [
        "k", "time_min", "c_abs", "T_abs", "h_abs", "c_dev", "T_dev", "h_dev",
        "Tc_abs", "F_abs", *[f"dhat_{i+1}" for i in range(nd)],
        "xs_c_dev", "xs_T_dev", "xs_h_dev", "us_Tc_dev", "us_F_dev",
        "c_offset_abs", "h_offset_abs", "controlled_offset_norm",
    ]
    csv_path = OUT_DIR / f"{design.name}_trajectory.csv"
    write_csv(csv_path, headers, rows)

    return {
        "hist": hist,
        "csv": csv_path,
        "K": K,
        "P_lqr": P_lqr,
        "eig_cl": eig_cl,
        "rho_cl": rho_cl,
        "L": L,
        "P_est": P_est,
        "eig_est": eig_est,
        "rho_est": rho_est,
        "final_y": final_y,
        "final_u": final_u,
        "final_dhat": final_dhat,
        "final_offsets": np.array([final_c_offset, final_T_offset, final_h_offset]),
        "final_controlled_offset_norm": final_controlled_norm,
    }


def plot_design(design: DisturbanceDesign, result: dict[str, Any]) -> list[Path]:
    hist = result["hist"]
    t = hist["time"]
    y = hist["y_abs"]
    u = hist["u_abs"]
    dhat = hist["dhat"]
    paths: list[Path] = []

    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    axes[0].plot(t, y[:, 0], label="c")
    axes[0].axhline(NOM.cs, linestyle="--", linewidth=1, label="c setpoint")
    axes[0].set_ylabel("c (kmol/m^3)")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(loc="best", fontsize=8)

    axes[1].plot(t, y[:, 1], label="T")
    axes[1].axhline(NOM.Ts, linestyle="--", linewidth=1, label="T nominal")
    axes[1].set_ylabel("T (K)")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(loc="best", fontsize=8)

    axes[2].plot(t, y[:, 2], label="h")
    axes[2].axhline(NOM.hs, linestyle="--", linewidth=1, label="h setpoint")
    axes[2].axvline(10, linestyle=":", linewidth=1, label="F0 step")
    axes[2].set_ylabel("h (m)")
    axes[2].set_xlabel("time (min)")
    axes[2].grid(True, alpha=0.3)
    axes[2].legend(loc="best", fontsize=8)
    fig.suptitle(f"Example 1.11 outputs - {design.name}")
    fig.tight_layout()
    path = OUT_DIR / f"{design.name}_outputs.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    paths.append(path)

    fig, axes = plt.subplots(2, 1, figsize=(10, 5.8), sharex=True)
    axes[0].plot(t[:-1], u[:-1, 0], label="Tc")
    axes[0].axhline(NOM.Tcs, linestyle="--", linewidth=1, label="Tc nominal")
    axes[0].set_ylabel("Tc (K)")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(loc="best", fontsize=8)

    axes[1].plot(t[:-1], u[:-1, 1], label="F")
    axes[1].axhline(NOM.Fs, linestyle="--", linewidth=1, label="F nominal")
    axes[1].axvline(10, linestyle=":", linewidth=1, label="F0 step")
    axes[1].set_ylabel("F (m^3/min)")
    axes[1].set_xlabel("time (min)")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(loc="best", fontsize=8)
    fig.suptitle(f"Example 1.11 manipulated inputs - {design.name}")
    fig.tight_layout()
    path = OUT_DIR / f"{design.name}_inputs.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    paths.append(path)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    for j in range(dhat.shape[1]):
        ax.plot(t, dhat[:, j], label=f"dhat {j+1}")
    ax.axvline(10, linestyle=":", linewidth=1, label="F0 step")
    ax.set_title(f"Estimated integrating disturbances - {design.name}")
    ax.set_xlabel("time (min)")
    ax.set_ylabel("disturbance estimate")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path = OUT_DIR / f"{design.name}_disturbance_estimates.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    paths.append(path)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(t, y[:, 0] - NOM.cs, label="c offset")
    ax.plot(t, y[:, 2] - NOM.hs, label="h offset")
    ax.axhline(0, linestyle="--", linewidth=1)
    ax.axvline(10, linestyle=":", linewidth=1, label="F0 step")
    ax.set_title(f"Controlled-variable offsets - {design.name}")
    ax.set_xlabel("time (min)")
    ax.set_ylabel("offset")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path = OUT_DIR / f"{design.name}_controlled_offsets.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    paths.append(path)

    return paths


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log: list[str] = []
    summary: dict[str, Any] = {
        "title": "Rawlings / Mayne / Diehl Example 1.11 sandbox",
        "out_dir": str(OUT_DIR),
        "nominal": arrs({
            "F0": NOM.F0, "T0": NOM.T0, "c0": NOM.c0, "r": NOM.r, "k0": NOM.k0,
            "E_over_R": NOM.E_over_R, "U": NOM.U, "rho": NOM.rho, "Cp": NOM.Cp,
            "dH": NOM.dH, "cs": NOM.cs, "Ts": NOM.Ts, "hs": NOM.hs,
            "Tcs": NOM.Tcs, "Fs": NOM.Fs,
        }),
        "linear_model": arrs({"A": A, "B": B, "C": C, "Bp_true": Bp_true, "H": H}),
        "cases": {},
    }

    log.extend([
        "Example 1.11 - More measured outputs than inputs and zero offset",
        "Rawlings / Mayne / Diehl Section 1.5.2 sandbox",
        "",
        "Core idea",
        "  The reactor has three measured outputs y=(c,T,h) but only two manipulated inputs u=(Tc,F).",
        "  Only two controlled variables are selected for zero offset: c and h.",
        "  Lemma 1.10 says zero-offset design generally needs nd=p integrating disturbances,",
        "  not nd=nc. Here p=3 measurements and nc=2 controlled variables.",
        "",
        "Textbook model data",
        "  Nonlinear plant states: c concentration, T reactor temperature, h liquid level.",
        "  Manipulated inputs: Tc coolant temperature, F outlet flowrate.",
        "  Unmeasured disturbance: inlet flowrate F0, stepped +10% at t=10 min.",
        "  Nominal steady state:",
        f"    cs={NOM.cs} kmol/m^3, Ts={NOM.Ts} K, hs={NOM.hs} m, Tcs={NOM.Tcs} K, Fs={NOM.Fs} m^3/min",
        "  Linear discrete model from the book, variables in deviation form:",
        "    A =", fmt(A),
        "    B =", fmt(B),
        "    C =", fmt(C),
        "    Bp true inlet-flow disturbance column =", fmt(Bp_true),
        "    H selects controlled variables c and h:", fmt(H),
    ])

    for design in make_designs():
        nd = design.Cd.shape[1]
        Dmat = detectability_rank_matrix(A, C, design.Bd, design.Cd)
        rank_D = int(matrix_rank(Dmat, tol=1e-9))
        required = A.shape[0] + nd
        pass_rank = rank_D == required
        log.extend([
            "",
            "=" * 94,
            f"Case: {design.name}",
            design.description,
            "",
            "Disturbance model",
            "  d(k+1) = d(k) + wd(k)",
            "  [x;d](k+1) = [[A,Bd],[0,I]][x;d](k) + [B;0]u(k)",
            "  y(k) = [C,Cd][x;d](k)",
            f"  nd={nd}, p={C.shape[0]}, nc={H.shape[0]}",
            "  Bd =", fmt(design.Bd),
            "  Cd =", fmt(design.Cd),
            "",
            "Detectability rank condition, equation 1.44",
            "  Need rank([[I-A, -Bd], [C, Cd]]) = n + nd.",
            "  rank matrix =", fmt(Dmat),
            f"  rank = {rank_D} / {required}",
            f"  passes? {pass_rank}",
            f"  Corollary 1.9 dimension check nd <= p: {nd} <= {C.shape[0]} is {nd <= C.shape[0]}",
            "  Textbook expectation: " + design.textbook_expected,
        ])

        case_summary: dict[str, Any] = {
            "description": design.description,
            "Bd": arrs(design.Bd),
            "Cd": arrs(design.Cd),
            "nd": nd,
            "rank_matrix": arrs(Dmat),
            "rank": rank_D,
            "required_rank": required,
            "passes_detectability_rank": pass_rank,
            "textbook_expected": design.textbook_expected,
        }

        if design.simulate:
            sim = simulate_design(design, log)
            plot_paths = plot_design(design, sim)
            case_summary.update({
                "csv": str(sim["csv"]),
                "plots": [str(p) for p in plot_paths],
                "K": arrs(sim["K"]),
                "rho_cl": sim["rho_cl"],
                "L": arrs(sim["L"]),
                "rho_est": sim["rho_est"],
                "final_y": arrs(sim["final_y"]),
                "final_u": arrs(sim["final_u"]),
                "final_dhat": arrs(sim["final_dhat"]),
                "final_offsets": arrs(sim["final_offsets"]),
                "final_controlled_offset_norm": sim["final_controlled_offset_norm"],
            })
        else:
            log.extend([
                "",
                "Part (b) conclusion",
                "  We do not simulate this design because the augmented estimator model is not detectable.",
                "  This reproduces the textbook result: adding an output integrator to h is ambiguous",
                "  because h already behaves as an integrator through the level balance.",
            ])

        summary["cases"][design.name] = case_summary

    # Add direct comparison lines between part a and c.
    a = summary["cases"].get("part_a_nd2_output_disturbances_on_c_and_h", {})
    c = summary["cases"].get("part_c_nd3_output_c_h_plus_input_F_disturbance", {})
    log.extend([
        "",
        "=" * 94,
        "Part (a) versus Part (c) comparison",
    ])
    if "final_offsets" in a and "final_offsets" in c:
        ao = np.asarray(a["final_offsets"], dtype=float)
        co = np.asarray(c["final_offsets"], dtype=float)
        log.extend([
            "  Part (a), nd=2 final offsets [c,T,h] = " + fmt(ao),
            "  Part (c), nd=3 final offsets [c,T,h] = " + fmt(co),
            f"  Part (a) controlled offset norm = {float(a['final_controlled_offset_norm']):.12g}",
            f"  Part (c) controlled offset norm = {float(c['final_controlled_offset_norm']):.12g}",
            "",
            "Engineering interpretation",
            "  Part (a) puts integrators only on the two controlled variables, but this leaves",
            "  a nonzero nullspace in the disturbance-estimator correction. The estimator can",
            "  stop changing while the output prediction error is not zero, so c and h can keep offset.",
            "  Part (b) tries three output integrators, but detectability fails because h is already",
            "  an integrating plant state. The estimator cannot distinguish level from a level bias.",
            "  Part (c) uses nd=p while avoiding the level-integrator ambiguity by making the third",
            "  disturbance enter through the outlet-flow input direction. This is detectable and",
            "  produces essentially zero offset in the maximum possible number of outputs: c and h.",
        ])

    log_path = OUT_DIR / "example_1_11_calculation_log.txt"
    log_path.write_text("\n".join(log) + "\n", encoding="utf-8")

    summary_path = OUT_DIR / "example_1_11_summary.json"
    summary_path.write_text(json.dumps(arrs(summary), indent=2) + "\n", encoding="utf-8")

    print("Example 1.11 run complete.")
    print(f"Output directory: {OUT_DIR}")
    print(f"Log: {log_path}")
    print(f"Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
