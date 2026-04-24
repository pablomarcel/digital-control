from __future__ import annotations
import numpy as np

_have_scipy = True
try:
    from scipy.signal import place_poles
except Exception:
    _have_scipy = False

_have_ctrl = True
try:
    import control as ctrl  # python-control
except Exception:
    _have_ctrl = False

def ctrb(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    n = A.shape[0]
    blocks = [B]
    X = B
    for _ in range(1, n):
        X = A @ X
        blocks.append(X)
    return np.hstack(blocks)

def obsv(A: np.ndarray, C: np.ndarray) -> np.ndarray:
    n = A.shape[0]
    blocks = [C]
    X = C
    for _ in range(1, n):
        X = X @ A
        blocks.append(X)
    return np.vstack(blocks)

def mat_pow(A: np.ndarray, k: int) -> np.ndarray:
    if k == 0:
        return np.eye(A.shape[0], dtype=complex)
    out = np.eye(A.shape[0], dtype=complex)
    base = A.copy()
    n = k
    while n:
        if n & 1:
            out = out @ base
        base = base @ base
        n >>= 1
    return out

def pretty_poly_from_roots(roots: np.ndarray) -> list[float]:
    coeffs = np.poly(roots)  # monic
    coeffs = np.real_if_close(coeffs, tol=1e-12)
    return [float(np.real(c)) for c in coeffs]

def pretty_poly_string(coeffs) -> str:
    coeffs = list(coeffs)
    n = len(coeffs) - 1
    terms: list[str] = []
    for i, a in enumerate(coeffs):
        p = n - i
        if p == 0:
            term = f"{a:+g}"
        elif p == 1:
            term = "z" if i == 0 else f"{a:+g} z"
        else:
            term = f"z^{p}" if i == 0 else f"{a:+g} z^{p}"
        terms.append(term)
    s = " ".join(terms)
    return s.replace("+ -", "- ").replace("  ", " ")

def match_pole_sets(lcl: np.ndarray, mu: np.ndarray) -> float:
    lcl = np.asarray(lcl).ravel()
    mu = np.asarray(mu).ravel()
    def dxy(x, Y): return float(np.min(np.abs(x - Y)))
    d1 = max(dxy(x, mu) for x in lcl) if len(lcl) else 0.0
    d2 = max(dxy(x, lcl) for x in mu) if len(mu) else 0.0
    return max(d1, d2)

def ackermann_siso(A: np.ndarray, B: np.ndarray, poles: np.ndarray) -> np.ndarray:
    n = A.shape[0]
    if B.shape[1] != 1:
        raise ValueError("Ackermann requires SISO (B is n×1).")
    coeffs = pretty_poly_from_roots(poles)  # [1, α1, ..., αn]
    alpha = coeffs[1:]
    M = ctrb(A, B)
    if np.linalg.matrix_rank(M) < n:
        raise ValueError("System not controllable; Ackermann invalid.")
    phi = mat_pow(A, n)
    for i in range(1, n):
        phi += alpha[i-1] * mat_pow(A, n - i)
    phi += alpha[-1] * np.eye(n, dtype=complex)
    e_nT = np.zeros((1, n), dtype=complex); e_nT[0, -1] = 1.0
    K = e_nT @ np.linalg.inv(M) @ phi
    return K

def eigenvector_method_siso(A: np.ndarray, B: np.ndarray, poles: np.ndarray) -> np.ndarray:
    n = A.shape[0]
    if B.shape[1] != 1:
        raise ValueError("Eigenvector method requires SISO.")
    Xi = []
    I = np.eye(n, dtype=complex)
    for mu in poles:
        Xi.append(np.linalg.solve(A - mu * I, B))
    X = np.hstack(Xi)
    if np.linalg.matrix_rank(X) < n:
        raise ValueError("Eigenvector matrix singular for given poles.")
    ones = np.ones((1, n), dtype=complex)
    return ones @ np.linalg.inv(X)

def place_method(A: np.ndarray, B: np.ndarray, poles: np.ndarray) -> np.ndarray:
    def real_if_possible(M):
        Mr = np.real_if_close(M, tol=1e-12)
        return Mr.real if np.all(np.isreal(Mr)) else M
    A_in = real_if_possible(A)
    B_in = real_if_possible(B)
    try:
        if not _have_scipy:
            raise RuntimeError("SciPy unavailable")
        res = place_poles(A_in, B_in, poles, method="YT")
        return np.array(res.gain_matrix, dtype=complex)
    except Exception:
        if _have_ctrl:
            K = ctrl.place(A, B, poles)
            return np.array(K, dtype=complex)
        if B.shape[1] == 1:
            return eigenvector_method_siso(A, B, poles)
        raise

def compute_K0(Acl: np.ndarray, B: np.ndarray, C: np.ndarray):
    n = Acl.shape[0]
    I = np.eye(n, dtype=complex)
    if np.min(np.abs(np.linalg.eigvals(Acl) - 1.0)) < 1e-10:
        return (np.zeros((B.shape[1], 1), dtype=complex),
                np.full((C.shape[0], B.shape[1]), np.nan, dtype=complex),
                "skipped (1 is an eigenvalue of Acl; (I-Acl) singular)")
    Sinv = np.linalg.inv(I - Acl)
    S = C @ Sinv @ B
    m = C.shape[0]
    ones = np.ones((m, 1), dtype=complex)
    K0, *_ = np.linalg.lstsq(S, ones, rcond=None)
    return K0, S, "ok"

def simulate_step(A: np.ndarray, B: np.ndarray, C: np.ndarray,
                  K: np.ndarray, K0: np.ndarray, N: int = 60):
    n = A.shape[0]
    m = C.shape[0]
    Acl = A - B @ K
    x = np.zeros((n, 1), dtype=complex)
    y = np.zeros((m, N), dtype=complex)
    kgrid = np.arange(N)
    u_ff = B @ K0
    for k in range(N):
        y[:, k:k+1] = C @ x
        x = Acl @ x + u_ff
    return kgrid, y
