
from __future__ import annotations
from typing import Optional, Tuple, List
import numpy as np
from numpy.linalg import eigvals, inv, matrix_rank
from scipy.signal import ss2tf

def realify_if_close(M: Optional[np.ndarray], tol: float = 1e-14) -> Optional[np.ndarray]:
    if M is None:
        return None
    if np.max(np.abs(getattr(M, "imag", 0.0))) < tol:
        return M.real.astype(float)
    return M

def controllability_matrix(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    n = A.shape[0]
    M = B.copy()
    Ak = np.eye(n, dtype=complex)
    for _ in range(1, n):
        Ak = Ak @ A
        M = np.concatenate((M, Ak @ B), axis=1)
    return M

def observability_matrix(A: np.ndarray, C: np.ndarray) -> np.ndarray:
    n = A.shape[0]
    N = C.copy()
    Ak = np.eye(n, dtype=complex)
    for _ in range(1, n):
        Ak = Ak @ A
        N = np.concatenate((N, C @ Ak), axis=0)
    return N

def charpoly_coeffs(A: np.ndarray) -> np.ndarray:
    den = np.poly(eigvals(A))
    return np.real_if_close(den[1:]).astype(complex)

def W_from_a(a: np.ndarray) -> np.ndarray:
    n = len(a)
    W = np.zeros((n, n), dtype=complex)
    for i in range(n):
        coeffs = list(a[: n - 1 - i])[::-1]
        row = coeffs + [1] + [0] * i
        W[i, : len(row)] = row
    return W

def to_ccf(A: np.ndarray, B: np.ndarray, C: Optional[np.ndarray], D: Optional[np.ndarray]):
    n = A.shape[0]
    if B is None or B.shape[1] != 1:
        raise ValueError("CCF requires SISO: B must be n×1.")
    M = controllability_matrix(A, B)
    if matrix_rank(M) < n:
        raise ValueError("System not controllable; CCF undefined.")
    a = charpoly_coeffs(A)
    W = W_from_a(a)
    T = M @ W
    Tinv = inv(T)
    Ahat = Tinv @ A @ T
    Bhat = Tinv @ B
    Chat = (C @ T) if C is not None else None
    Dhat = D
    return Ahat, Bhat, Chat, Dhat, T, a

def to_ocf(A: np.ndarray, B: Optional[np.ndarray], C: np.ndarray, D: Optional[np.ndarray]):
    n = A.shape[0]
    if C is None or C.shape[0] != 1:
        raise ValueError("OCF requires SISO output: C must be 1×n.")
    Ad, Bd = A.T, C.T
    M = controllability_matrix(Ad, Bd)
    if matrix_rank(M) < n:
        raise ValueError("Dual system not controllable; OCF undefined (system not observable).")
    a = charpoly_coeffs(Ad)
    W = W_from_a(a)
    Td = M @ W
    Q = inv(Td).T
    Qinv = inv(Q)
    Ahat = Qinv @ A @ Q
    Chat = C @ Q
    Bhat = (Qinv @ B) if B is not None else None
    Dhat = D
    return Ahat, Bhat, Chat, Dhat, Q, a

def to_diag(A: np.ndarray, B: Optional[np.ndarray], C: Optional[np.ndarray], D: Optional[np.ndarray], tol=1e-8):
    vals, vecs = np.linalg.eig(A)
    for i in range(len(vals)):
        if np.min(np.abs(vals[i] - np.delete(vals, i))) < tol:
            raise ValueError("A does not have distinct eigenvalues (within tolerance); use Jordan.")
    P, Pinv = vecs, np.linalg.inv(vecs)
    Ahat = Pinv @ A @ P
    Bhat = Pinv @ B if B is not None else None
    Chat = C @ P if C is not None else None
    Dhat = D
    return Ahat, Bhat, Chat, Dhat, P

def to_jordan_sympy(A: np.ndarray, B: Optional[np.ndarray], C: Optional[np.ndarray], D: Optional[np.ndarray]):
    import sympy as sp
    A_sym = sp.Matrix(A)
    try:
        A_sym = sp.nsimplify(A_sym, rational=True, maxsteps=50)
    except Exception:
        pass
    P, J = A_sym.jordan_form()
    S = np.array(P, dtype=complex)
    Sinv = np.array(P.inv(), dtype=complex)
    Jnp = np.array(J, dtype=complex)
    Bhat = Sinv @ B if B is not None else None
    Chat = (C @ S) if C is not None else None
    Dhat = D
    return Jnp, Bhat, Chat, Dhat, S

def siso_tf_coeffs(A: np.ndarray, B: np.ndarray, C: np.ndarray, D: Optional[np.ndarray]):
    if B is None or C is None:
        raise ValueError("Need B and C for SISO transfer function.")
    if B.shape[1] != 1 or C.shape[0] != 1:
        raise ValueError("SISO only for transfer function coefficients.")
    Ar, Br, Cr = realify_if_close(A), realify_if_close(B), realify_if_close(C)
    Dr = realify_if_close(D) if D is not None else 0.0
    num, den = ss2tf(Ar, Br, Cr, Dr)
    b = np.array(num[0], dtype=complex)
    a = np.array(den, dtype=complex)
    if abs(a[0] - 1.0) > 1e-12:
        b = b / a[0]; a = a / a[0]
    return b, a[1:]
