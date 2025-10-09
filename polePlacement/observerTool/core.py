
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple

import numpy as np
import control as ct
from numpy.linalg import inv

from .io import parse_matrix, parse_poles
from .utils import eigvals_sorted


def _force_col(M: np.ndarray) -> np.ndarray:
    M = np.asarray(M)
    if M.ndim == 1:
        return M.reshape(-1, 1)
    if M.shape[0] == 1 and M.shape[1] > 1:
        return M.T
    return M


def _place_dual(A: np.ndarray, C: np.ndarray, poles: List[complex], method: str) -> np.ndarray:
    L = None
    if method.lower() == "place":
        try:
            L = ct.place(A.T, C.T, poles).T
        except Exception:
            L = None
    if L is None:
        try:
            L = ct.acker(A.T, C.T, poles).T
        except Exception:
            eps = 1e-6
            jpoles = [p + (i * eps) for i, p in enumerate(poles)]
            L = ct.place(A.T, C.T, jpoles).T
    return _force_col(np.asarray(L, dtype=float))


# ---- full / current ----

def design_prediction_observer(A, C, poles, method="place"):
    return _place_dual(A, C, poles, method)


def design_current_observer(A, C, poles, method="place"):
    CA = C @ A
    return _place_dual(A, CA, poles, method)


# ---- DLQE ----

def dlqe_gain(A, G, C, Qn, Rn):
    L, P, E = ct.dlqe(A, G, C, Qn, Rn)
    return _force_col(L), P, E


# ---- minimum-order ----

@dataclass
class MinObsDesign:
    Ke: np.ndarray
    T: np.ndarray
    Ti: np.ndarray
    blocks: Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]
    err_poles: np.ndarray


def _measured_form(A: np.ndarray, B: np.ndarray, C: np.ndarray) -> Tuple[np.ndarray, np.ndarray, Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]]:
    m, n = C.shape
    T1 = C.T @ inv(C @ C.T)  # right-inverse so C*T1=I
    U, S, Vt = np.linalg.svd(C)
    rank = np.sum(S > 1e-12)
    if rank != m:
        raise ValueError("C must have full row rank.")
    V = Vt.T
    N = V[:, m:]                # nullspace(C)
    T = np.hstack([T1, N])      # CT = [I 0]
    Ti = inv(T)
    A_ = Ti @ A @ T
    B_ = Ti @ B
    Gaa = A_[:m, :m]; Gab = A_[:m, m:]
    Gba = A_[m:, :m]; Gbb = A_[m:, m:]
    Ha = B_[:m, :];  Hb = B_[m:, :]
    return T, Ti, (A_, B_), (Gaa, Gab, Gba, Gbb, Ha, Hb)


def design_minimum_order_observer(A: np.ndarray, B: np.ndarray, C: np.ndarray, poles: List[complex], method="place") -> MinObsDesign:
    T, Ti, _, blocks = _measured_form(A, B, C)
    Gaa, Gab, Gba, Gbb, Ha, Hb = blocks
    Ke = _place_dual(Gbb, Gab, poles, method)
    Aerr = Gbb - Ke @ Gab
    return MinObsDesign(Ke=Ke, T=T, Ti=Ti, blocks=blocks, err_poles=np.linalg.eigvals(Aerr))


def minobs_step(Ke, blocks, yk, uk, eta_k):
    Ke = _force_col(Ke)
    yk = np.atleast_2d(yk); uk = np.atleast_2d(uk); eta_k = np.atleast_2d(eta_k)
    Gaa, Gab, Gba, Gbb, Ha, Hb = blocks
    Aerr = Gbb - Ke @ Gab
    Fy = (Aerr @ Ke + Gba - Ke @ Gaa)
    Fu = (Hb - Ke @ Ha)
    eta_next = Aerr @ eta_k + Fy @ yk + Fu @ uk
    xbh_next = eta_next + Ke @ yk
    return eta_next, xbh_next


def reconstruct_xhat_from_minobs(T: np.ndarray, yk: np.ndarray, xbh: np.ndarray) -> np.ndarray:
    return T @ np.vstack([yk, xbh])


# ---- K0 ----

def k0_state(A: np.ndarray, B: np.ndarray, C: np.ndarray, K: np.ndarray) -> float:
    M = C @ inv(np.eye(A.shape[0]) - (A - B @ K)) @ B  # 1x1
    M = float(np.squeeze(M))
    return float(1.0 / M)


def k0_ogata(A: np.ndarray, B: np.ndarray, C: np.ndarray, K: np.ndarray, L: np.ndarray, extra_gain: float | None = None) -> float:
    Aaug = np.block([[A,           -B @ K],
                     [L @ C,  A - B @ K - L @ C]])
    Caug = np.hstack([C, np.zeros_like(C)])
    Baug = np.vstack([B, B])  # K0 multiplies both inputs equally
    H1 = float(np.squeeze(Caug @ inv(np.eye(Aaug.shape[0]) - Aaug) @ Baug))
    if extra_gain is None:
        extra_gain = 1.0
    return float(1.0 / (H1 * extra_gain))


# ---- Ke selection ----

def ke_rule_of_thumb(A, C, plant_poles: Iterable[complex], speedup: float = 5.0, method="place"):
    poles = []
    for p in plant_poles:
        r = min(0.2, abs(p) ** speedup)
        poles.append(r * np.exp(1j * np.angle(p)))
    return _place_dual(A, C, poles, method), poles


def ke_grid_search(A, C, B, K, pole_grid: List[List[complex]], steps=200, seed=0):
    best = (np.inf, None, None)
    n = A.shape[0]
    for poles in pole_grid:
        try:
            L = _place_dual(A, C, poles, "place")
        except Exception:
            continue
        x = np.zeros((n, 1))
        xh = np.zeros_like(x)
        mse = 0.0
        for _ in range(steps):
            u = -K @ xh
            y = C @ x
            x = A @ x + B @ u
            xh = A @ xh + B @ u + L @ (y - C @ xh)
            mse += float(np.mean((x - xh) ** 2))
        mse /= steps
        if mse < best[0]:
            best = (mse, poles, L)
    return best


# ---- simulation ----

def simulate_full_observer(A, B, C, K, L, x0=None, xh0=None, N=60, r=None, Ts=1.0, K0=None):
    A = np.asarray(A, float); B = np.asarray(B, float); C = np.asarray(C, float)
    K = np.asarray(K, float); L = _force_col(np.asarray(L, float))
    n = A.shape[0]
    x = np.zeros((n, 1)) if x0 is None else np.asarray(x0, float).reshape(n, 1)
    xh = np.zeros_like(x) if xh0 is None else np.asarray(xh0, float).reshape(n, 1)
    if r is None:
        r = np.zeros((N, 1))
    r = np.asarray(r, float).reshape(N, 1)
    K0 = 0.0 if K0 is None else float(K0)
    xs, xhs, ys, us = [], [], [], []
    for k in range(N):
        y = C @ x
        u = K0 * r[k] - K @ xh
        x = A @ x + B @ u
        xh = A @ xh + B @ u + L @ (y - C @ xh)
        xs.append(x.copy()); xhs.append(xh.copy()); ys.append(y.copy()); us.append(u.copy())
    t = Ts * np.arange(N)
    return dict(t=t, x=xs, xhat=xhs, y=ys, u=us)
