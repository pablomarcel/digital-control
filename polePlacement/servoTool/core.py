from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Tuple
import numpy as np
import scipy.linalg as la

def to_real_if_close(a: np.ndarray, tol: float = 1e-12) -> np.ndarray:
    if np.iscomplexobj(a) and np.all(np.abs(a.imag) < tol):
        return a.real
    return a

def ctrb(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    n = A.shape[0]
    blocks = [B]
    Ap = np.eye(n)
    for _ in range(1, n):
        Ap = Ap @ A
        blocks.append(Ap @ B)
    return np.hstack(blocks)

def poly_from_roots(roots: List[complex]) -> np.ndarray:
    p = np.array([1.0], dtype=complex)
    for r in roots:
        p = np.convolve(p, np.array([1.0, -complex(r)], dtype=complex))
    return p

def acker(A: np.ndarray, B: np.ndarray, desired_poles: List[complex]) -> np.ndarray:
    n = A.shape[0]
    B = np.atleast_2d(B)
    if B.shape[0] != n:
        B = B.T
    if B.shape[1] > 1:
        idx = None
        for j in range(B.shape[1]):
            if np.linalg.matrix_rank(ctrb(A, B[:, [j]])) == n:
                idx = j; break
        if idx is None:
            raise ValueError('System not controllable (acker).')
        Buse = B[:, [idx]]
    else:
        Buse = B
    Co = ctrb(A, Buse)
    if np.linalg.matrix_rank(Co) < n:
        raise ValueError('System not controllable (acker).')

    coeffs = poly_from_roots(desired_poles)
    powers = [np.eye(n, dtype=complex)]
    for _ in range(1, n+1):
        powers.append(powers[-1] @ A)
    phiA = np.zeros_like(A, dtype=complex)
    for i in range(n):
        phiA += coeffs[i] * powers[n - i]
    phiA += coeffs[n] * np.eye(n, dtype=complex)

    eT = np.zeros((1, n), dtype=complex); eT[0, -1] = 1.0
    K = eT @ la.solve(Co, phiA)
    if B.shape[1] > 1:
        Kfull = np.zeros((1, B.shape[1]), dtype=complex); Kfull[0, idx] = K
        K = Kfull
    return to_real_if_close(K)

def place_wrapper(A: np.ndarray, B: np.ndarray, poles: List[complex], method: str) -> np.ndarray:
    m = (method or 'acker').lower()
    if m == 'acker':
        return acker(A, B, poles)
    try:
        import control as ct  # type: ignore
        if m == 'place':
            return to_real_if_close(ct.place(A, B, poles))
        elif m == 'acker_ct':
            return to_real_if_close(ct.acker(A, B, poles))
    except Exception:
        pass
    return acker(A, B, poles)

def design_servo_ogata(G: np.ndarray, H: np.ndarray, C: np.ndarray,
                       poles: Optional[List[complex]] = None,
                       method: str = 'acker') -> Tuple[np.ndarray, np.ndarray]:
    G = np.array(G, dtype=complex); H = np.array(H, dtype=complex); C = np.array(C, dtype=complex)
    n = G.shape[0]
    m = C.shape[0] if C.ndim == 2 else 1
    if poles is None:
        poles = [0.0] * (n + m)
    Ghat = np.block([[G, H],
                     [np.zeros((m, n), dtype=complex), np.zeros((m, m), dtype=complex)]])
    Hhat = np.vstack([np.zeros((n, m), dtype=complex), np.eye(m, dtype=complex)])
    Khat = place_wrapper(Ghat, Hhat, poles, method)
    M = np.block([[G - np.eye(n, dtype=complex), H],
                  [-C @ G,                      C @ H]])
    RHS = Khat + np.hstack([np.zeros((m, n), dtype=complex), np.eye(m, dtype=complex)])
    K = RHS @ la.inv(M)
    K2 = K[:, :n]
    K1 = -K[:, n:]
    return to_real_if_close(K1), to_real_if_close(K2)

def design_servo_aug(G: np.ndarray, H: np.ndarray, C: np.ndarray,
                     poles: Optional[List[complex]] = None,
                     method: str = 'acker') -> Tuple[np.ndarray, np.ndarray]:
    G = np.array(G, dtype=complex); H = np.array(H, dtype=complex); C = np.array(C, dtype=complex)
    n = G.shape[0]
    m = C.shape[0] if C.ndim == 2 else 1
    A_aug = np.block([[G, np.zeros((n, m), dtype=complex)],
                      [-C, np.eye(m, dtype=complex)]])
    B_aug = np.vstack([H, np.zeros((m, H.shape[1]), dtype=complex)])
    if poles is None:
        poles = [0.0] * (n + m)
    K_aug = place_wrapper(A_aug, B_aug, poles, method)
    K2 = K_aug[:, :n]; K1 = -K_aug[:, n:]
    return to_real_if_close(K1), to_real_if_close(K2)

@dataclass
class MinObserver:
    Ke: np.ndarray
    T:  np.ndarray

def right_inverse(C: np.ndarray) -> np.ndarray:
    Ct = C.conj().T
    return Ct @ la.inv(C @ Ct)

def measured_form_T(C: np.ndarray, n: int, m: int) -> np.ndarray:
    X = right_inverse(C)
    N = la.null_space(C)
    if N.shape[1] != (n - m):
        Q, _ = la.qr(np.hstack([X, np.random.randn(n, n-m)]))
        N = Q[:, m:]
    T = np.hstack([X, N])
    return T

def design_min_observer(G: np.ndarray, H: np.ndarray, C: np.ndarray,
                        poles: Optional[List[complex]] = None,
                        method: str = 'acker') -> MinObserver:
    G = np.array(G, dtype=complex); H = np.array(H, dtype=complex); C = np.array(C, dtype=complex)
    n = G.shape[0]; m = C.shape[0] if C.ndim == 2 else 1
    if poles is None:
        poles = [0.0] * (n - m)
    T = measured_form_T(C, n, m); Ti = la.inv(T)
    Gbar = Ti @ G @ T; Hbar = Ti @ H
    Gaa = Gbar[:m, :m]; Gab = Gbar[:m, m:]
    Gba = Gbar[m:, :m]; Gbb = Gbar[m:, m:]
    Ke = place_wrapper(Gbb.T, Gab.T, poles, method).T
    return MinObserver(Ke=to_real_if_close(Ke), T=to_real_if_close(T))

@dataclass
class SimOut:
    y: list[float]
    u: list[float]
    k0_u: float

def simulate_servo(G: np.ndarray, H: np.ndarray, C: np.ndarray,
                   K1: np.ndarray, K2: np.ndarray,
                   N: int = 10, r_type: str = 'step',
                   use_observer: bool = False,
                   minobs: Optional[MinObserver] = None,
                   observer_mode: str = 'current') -> SimOut:
    G = np.array(G, dtype=float); H = np.array(H, dtype=float); C = np.array(C, dtype=float)
    K1 = np.array(K1, dtype=float).reshape(1, -1)
    K2 = np.array(K2, dtype=float).reshape(1, -1)

    n = G.shape[0]; m = C.shape[0] if C.ndim == 2 else 1
    x = np.zeros((n, 1))
    v = np.zeros((m, 1))
    y_list: list[float] = []
    u_list: list[float] = []

    if r_type.lower() not in ('step', 'ramp'):
        raise ValueError("ref must be 'step' or 'ramp'.")

    use_obs = bool(use_observer)
    if use_obs:
        if minobs is None:
            raise ValueError('use_observer=True requires minobs (Ke,T).')
        T = np.array(minobs.T, dtype=float); Ti = la.inv(T); Ke = np.array(minobs.Ke, dtype=float)
        Gbar = Ti @ G @ T; Hbar = Ti @ H
        Gaa = Gbar[:m, :m]; Gab = Gbar[:m, m:]
        Gba = Gbar[m:, :m]; Gbb = Gbar[m:, m:]
        Ha  = Hbar[:m, :];  Hb  = Hbar[m:, :]
        xi_hat_b = np.zeros((n - m, 1))
        observer_mode = observer_mode.lower()

    def r_of(k: int) -> np.ndarray:
        if r_type.lower() == 'step':
            return np.ones((m, 1))
        return float(k) * np.ones((m, 1))

    u0 = (-K2 @ x + K1 @ v).item()

    for k in range(N):
        y = (C @ x).item()
        y_list.append(y)

        if use_obs:
            xi_a = np.array([[y]])
            x_hat = T @ np.vstack([xi_a, xi_hat_b])
            u = (-K2 @ x_hat + K1 @ v).item()
        else:
            u = (-K2 @ x + K1 @ v).item()
        u_list.append(u)

        x_next = G @ x + H * u
        y_next = (C @ x_next).item()

        v = v + r_of(k + 1) - y_next

        if use_obs:
            if observer_mode == 'current':
                xi_hat_b = (Gbb - Ke @ Gab) @ xi_hat_b + (Gba - Ke @ Gaa) @ np.array([[y]]) + (Hb - Ke @ Ha) * u + Ke * y_next
            else:
                xi_hat_b = (Gbb - Ke @ Gab) @ xi_hat_b + (Gba - Ke @ Gaa) @ np.array([[y]]) + (Hb - Ke @ Ha) * u

        x = x_next

    return SimOut(y=y_list, u=u_list, k0_u=u0)
