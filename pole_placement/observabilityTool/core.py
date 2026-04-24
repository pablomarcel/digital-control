
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from numpy.linalg import eig, svd
from scipy.linalg import expm, solve_continuous_lyapunov as lyap

try:
    import control as ct
except Exception:
    ct = None

def observability_matrix(A: np.ndarray, C: np.ndarray, horizon: Optional[int] = None) -> np.ndarray:
    n = A.shape[0]
    if horizon is None:
        horizon = n
    blocks = []
    Ak = np.eye(n, dtype=complex)
    for _ in range(horizon):
        blocks.append(C @ Ak)
        Ak = Ak @ A
    return np.vstack(blocks)

def rank_numeric(M: np.ndarray, tol: Optional[float] = None) -> int:
    _, s, _ = svd(M)
    if tol is None:
        eps = np.finfo(float).eps
        tol = max(M.shape) * eps * (s[0] if s.size else 0.0)
    return int(np.sum(s > tol))

def stable_ct(A: np.ndarray) -> bool:
    vals, _ = eig(A)
    return bool(np.all(np.real(vals) < 0.0))

def stable_dt(A: np.ndarray) -> bool:
    vals, _ = eig(A)
    return bool(np.all(np.abs(vals) < 1.0))

def pbh_observable(A: np.ndarray, C: np.ndarray) -> Tuple[bool, List[Dict[str, Any]]]:
    n = A.shape[0]
    vals, _ = eig(A)
    details = []
    ok_all = True
    for lam in vals:
        M = np.hstack((lam.conjugate() * np.eye(n, dtype=complex) - A.conjugate().T, C.conjugate().T))
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

def _real_if_close_for_control(X: np.ndarray) -> np.ndarray:
    Xr = np.real_if_close(X, tol=1000)
    if np.iscomplexobj(Xr):
        return X
    return Xr.astype(float)

def gramian_observability_ct(A: np.ndarray, C: np.ndarray) -> Optional[np.ndarray]:
    if not stable_ct(A):
        return None
    if ct is not None:
        try:
            n = A.shape[0]
            A0 = _real_if_close_for_control(A)
            C0 = _real_if_close_for_control(C)
            sys = ct.ss(A0, np.zeros((n, 1)), C0, np.zeros((C.shape[0], 1)))
            W = ct.gram(sys, 'o')
            return np.array(W, dtype=complex)
        except Exception:
            pass
    Q = C.conjugate().T @ C
    return lyap(_real_if_close_for_control(A.conjugate().T), -_real_if_close_for_control(Q)).conjugate().T

def gramian_observability_dt(A: np.ndarray, C: np.ndarray) -> Optional[np.ndarray]:
    if not stable_dt(A):
        return None
    if ct is not None:
        try:
            n = A.shape[0]
            A0 = _real_if_close_for_control(A)
            C0 = _real_if_close_for_control(C)
            sys = ct.ss(A0, np.zeros((n, 1)), C0, np.zeros((C.shape[0], 1)), dt=True)
            W = ct.gram(sys, 'o')
            return np.array(W, dtype=complex)
        except Exception:
            pass
    n = A.shape[0]
    Q = C.conjugate().T @ C
    K = np.eye(n * n, dtype=complex) - np.kron(A.T, A.conjugate())
    w = np.linalg.solve(K, Q.reshape(n * n, order="F"))
    return w.reshape((n, n), order="F")

def finite_gramian_dt(A: np.ndarray, C: np.ndarray, N: int) -> np.ndarray:
    if N <= 0:
        raise ValueError("--finite-dt requires N >= 1")
    n = A.shape[0]
    W = np.zeros((n, n), dtype=complex)
    Ak = np.eye(n, dtype=complex)
    Q = C.conjugate().T @ C
    for _ in range(N):
        W += Ak.conjugate().T @ Q @ Ak
        Ak = A @ Ak
    return W

def finite_gramian_ct(A: np.ndarray, C: np.ndarray, T: float) -> np.ndarray:
    if T <= 0.0:
        raise ValueError("--finite-ct requires T > 0")
    n = A.shape[0]
    Q = C.conjugate().T @ C
    M = np.block([
        [-A.conjugate().T,  Q],
        [np.zeros((n, n), dtype=complex), A]
    ])
    E = expm(M * T)
    Phi12 = E[:n, n:]
    Phi22 = E[n:, n:]
    W = Phi12 @ np.linalg.inv(Phi22)
    return 0.5 * (W + W.conjugate().T)

def minreal_observable(A: np.ndarray, C: np.ndarray, tol: Optional[float] = None):
    n = A.shape[0]
    Obsv = observability_matrix(A, C, horizon=n)
    U, s, Vh = svd(Obsv)
    if tol is None:
        eps = np.finfo(float).eps
        tol = max(Obsv.shape) * eps * (s[0] if s.size else 0.0)
    r = int(np.sum(s > tol))
    V = Vh.conjugate().T
    Vo = V[:, :r]
    Vu = V[:, r:]
    T = np.hstack((Vo, Vu))
    Abar = T.conjugate().T @ A @ T
    Cbar = C @ T
    Ar = Abar[:r, :r]
    Cr = Cbar[:, :r]
    return Ar, Cr, T
