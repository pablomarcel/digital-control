from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from numpy.linalg import eig, svd
from scipy.linalg import solve_continuous_lyapunov as lyap
from scipy.linalg import expm

try:
    import control as ct
except Exception:
    ct = None

try:
    import sympy as sp
except Exception:
    sp = None

from .utils import stable_ct, stable_dt, rank_numeric, real_if_close_for_control

def controllability_matrix(A: np.ndarray, B: np.ndarray, horizon: Optional[int] = None) -> np.ndarray:
    n = A.shape[0]
    if horizon is None:
        horizon = n
    blocks = []
    AkB = B.copy()
    for k in range(horizon):
        blocks.append(B if k == 0 else AkB)
        AkB = A @ AkB
    return np.hstack(blocks)

def output_controllability_matrix(A: np.ndarray, B: np.ndarray, C: np.ndarray,
                                 horizon: Optional[int] = None,
                                 D: Optional[np.ndarray] = None) -> np.ndarray:
    n = A.shape[0]
    if horizon is None:
        horizon = n
    blocks = []
    if D is not None:
        blocks.append(D)
    AkB = B.copy()
    for k in range(horizon):
        blocks.append(C @ (B if k == 0 else AkB))
        AkB = A @ AkB
    return np.hstack(blocks)

def pbh_controllable(A: np.ndarray, B: np.ndarray) -> Tuple[bool, List[Dict[str, Any]]]:
    n = A.shape[0]
    vals, _ = eig(A)
    details = []
    ok_all = True
    for lam in vals:
        M = np.hstack((lam * np.eye(n, dtype=complex) - A, B))
        _, s, _ = svd(M)
        tol = max(M.shape) * np.finfo(float).eps * (s[0] if s.size else 0.0)
        r = int(np.sum(s > tol))
        sigma_min = float(s[-1]) if s.size else 0.0
        ok = (r == n)
        ok_all = ok_all and ok
        details.append({
            "lambda": complex(lam),
            "rank": int(r),
            "sigma_min": sigma_min,
            "pass": bool(ok),
        })
    return bool(ok_all), details

def gramian_controllability_ct(A: np.ndarray, B: np.ndarray) -> Optional[np.ndarray]:
    if not stable_ct(A):
        return None
    if ct is not None:
        try:
            n = A.shape[0]
            A0 = real_if_close_for_control(A)
            B0 = real_if_close_for_control(B)
            sys = ct.ss(A0, B0, np.eye(n), np.zeros((n, B.shape[1])))
            W = ct.gram(sys, 'c')
            return np.array(W, dtype=complex)
        except Exception:
            pass
    Q = B @ B.conj().T
    return lyap(real_if_close_for_control(A), -np.real_if_close(Q))

def gramian_controllability_dt(A: np.ndarray, B: np.ndarray) -> Optional[np.ndarray]:
    if not stable_dt(A):
        return None
    if ct is not None:
        try:
            n = A.shape[0]
            A0 = real_if_close_for_control(A)
            B0 = real_if_close_for_control(B)
            sys = ct.ss(A0, B0, np.eye(n), np.zeros((n, B.shape[1])), dt=True)
            W = ct.gram(sys, 'c')
            return np.array(W, dtype=complex)
        except Exception:
            pass
    n = A.shape[0]
    Q = B @ B.conj().T
    K = np.eye(n * n, dtype=complex) - np.kron(A, A)
    w = np.linalg.solve(K, Q.reshape(n * n, order="F"))
    return w.reshape((n, n), order="F")

def finite_gramian_dt(A: np.ndarray, B: np.ndarray, N: int) -> np.ndarray:
    if N <= 0:
        raise ValueError("--finite-dt requires N >= 1")
    n = A.shape[0]
    W = np.zeros((n, n), dtype=complex)
    Ak = np.eye(n, dtype=complex)
    Q = B @ B.conj().T
    for _ in range(N):
        W += Ak @ Q @ Ak.conj().T
        Ak = A @ Ak
    return W

def finite_gramian_ct(A: np.ndarray, B: np.ndarray, T: float) -> np.ndarray:
    if T <= 0.0:
        raise ValueError("--finite-ct requires T > 0")
    n = A.shape[0]
    Q = B @ B.conj().T
    M = np.block([
        [A,              Q],
        [np.zeros((n,n), dtype=complex), -A.conj().T]
    ])
    E = expm(M * T)
    Phi12 = E[:n, n:]
    Phi22 = E[n:, n:]
    W = Phi12 @ np.linalg.inv(Phi22)
    return 0.5 * (W + W.conj().T)

def minreal_controllable(A: np.ndarray, B: np.ndarray, tol: Optional[float] = None):
    n = A.shape[0]
    Ctrb = controllability_matrix(A, B, horizon=n)
    U, s, _ = svd(Ctrb)
    if tol is None:
        eps = np.finfo(float).eps
        tol = max(Ctrb.shape) * eps * (s[0] if s.size else 0.0)
    r = int(np.sum(s > tol))
    Tc = U[:, :r]
    Ar = Tc.conj().T @ A @ Tc
    Br = Tc.conj().T @ B
    return Ar, Br, Tc

def sympy_rank_ctrb(A: np.ndarray, B: np.ndarray, horizon: Optional[int]) -> Optional[int]:
    if sp is None:
        return None
    A_sym = sp.Matrix(A.tolist())
    B_sym = sp.Matrix(B.tolist())
    n = A.shape[0]
    n_h = n if horizon is None else horizon
    C_sym = B_sym
    Ak = sp.eye(n)
    for _ in range(1, n_h):
        Ak = Ak * A_sym
        C_sym = C_sym.row_join(Ak * B_sym)
    return int(C_sym.rank())
