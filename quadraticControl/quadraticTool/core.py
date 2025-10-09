from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional, List
import numpy as np
from numpy.typing import ArrayLike
import scipy.linalg as la


# ----------------------------
# Helpers
# ----------------------------

def _as_mat(x: ArrayLike) -> np.ndarray:
    a = np.asarray(x, dtype=float)
    if a.ndim == 0:
        a = a.reshape(1, 1)
    return a

def _as_vec(x: ArrayLike) -> np.ndarray:
    a = np.asarray(x, dtype=float)
    return a.reshape(-1, 1)

def _scalar(x) -> float:
    return float(np.asarray(x, dtype=float).reshape(-1)[0])

def substitute_params_matrix(template: ArrayLike, params: Dict[str, float]) -> np.ndarray:
    """
    Substitute numeric values into a matrix template that may contain strings
    (expressions or parameter names). Safe locals are only the provided params.
    """
    arr = np.array(template, dtype=object)
    it = np.nditer(arr, flags=["multi_index", "refs_ok"], op_flags=["readwrite"])
    safe_locals = {k: float(v) for k, v in params.items()}
    for _ in it:
        idx = it.multi_index
        v = arr[idx]
        if isinstance(v, (int, float, np.floating)):
            arr[idx] = float(v)
        elif isinstance(v, str):
            s = v.strip()
            if s in safe_locals:
                arr[idx] = safe_locals[s]
            else:
                # Evaluate simple arithmetic/formulas with only provided names
                arr[idx] = float(eval(s, {}, safe_locals))
        else:
            arr[idx] = float(v)
    return arr.astype(float)


# ----------------------------
# Finite-horizon LQR
# ----------------------------

@dataclass
class FHResult:
    P_seq: List[np.ndarray]
    K_seq: List[np.ndarray]
    x_seq: List[np.ndarray]
    u_seq: List[np.ndarray]
    J: float

class FiniteHorizonLQR:
    def solve(
        self,
        G: ArrayLike,
        H: ArrayLike,
        Q: ArrayLike,
        R: ArrayLike,
        N: int,
        S: Optional[ArrayLike] = None,
        M: Optional[ArrayLike] = None,
        x0: Optional[ArrayLike] = None,
    ) -> FHResult:
        G = _as_mat(G); H = _as_mat(H); Q = _as_mat(Q); R = _as_mat(R)
        n = G.shape[0]; m = H.shape[1]
        if S is None:
            S = np.zeros((n, n))
        S = _as_mat(S)
        if M is None:
            M = np.zeros((n, m))
        else:
            M = _as_mat(M)

        Rin = la.inv(R)
        Qhat = Q - M @ Rin @ M.T
        Ghat = G - H @ Rin @ M.T

        P_seq: List[np.ndarray] = [None] * (N + 1)  # type: ignore
        K_seq: List[np.ndarray] = []

        P_next = S.copy()
        P_seq[N] = P_next.copy()

        for _k in range(N - 1, -1, -1):
            S_k = R + H.T @ P_next @ H
            Sinv = la.inv(S_k)
            term = Ghat.T @ P_next @ H @ Sinv @ H.T @ P_next @ Ghat
            P_k = Qhat + Ghat.T @ P_next @ Ghat - term
            P_seq[_k] = P_k.copy()
            K_k = Sinv @ (H.T @ P_next @ G + M.T)
            K_seq.insert(0, K_k.copy())
            P_next = P_k

        x0 = _as_vec(np.zeros(n) if x0 is None else x0)
        x_seq: List[np.ndarray] = [x0.copy()]
        u_seq: List[np.ndarray] = []
        for k in range(N):
            u = -K_seq[k] @ x_seq[-1]
            x_next = G @ x_seq[-1] + H @ u
            u_seq.append(u.copy()); x_seq.append(x_next.copy())

        J = float(0.5 * (x_seq[0].T @ P_seq[0] @ x_seq[0]).reshape(()))
        return FHResult(P_seq=P_seq, K_seq=K_seq, x_seq=x_seq, u_seq=u_seq, J=J)


# ----------------------------
# Continuous-to-discrete (Ogata Ex. 8-2 style)
# ----------------------------

@dataclass
class CTDiscretizeResult:
    G: np.ndarray
    H: np.ndarray
    Q1: np.ndarray
    M1: np.ndarray
    R1: np.ndarray

class CTtoDTWeights:
    def siso_ogata(self, a: float, b: float, T: float) -> CTDiscretizeResult:
        ea = np.exp(a * T)
        G = np.array([[ea]], dtype=float)
        if a != 0.0:
            H = np.array([[b / a * (ea - 1)]], dtype=float)
        else:
            H = np.array([[b * T]], dtype=float)
        if a == 0.0:
            Q1 = np.array([[T]], dtype=float)
            M1 = np.array([[0.5 * b * T * T]], dtype=float)
            R1 = np.array([[T + b * b * T ** 3 / 3]], dtype=float)
        else:
            Q1 = np.array([[(np.exp(2 * a * T) - 1) / (2 * a)]], dtype=float)
            M1 = np.array([[b / (2 * a * a) * (np.exp(a * T) - 1) ** 2]], dtype=float)
            R1 = np.array([[T + (b * b / (2 * a ** 3)) * ((np.exp(a * T) - 3) * (np.exp(a * T) - 1) + 2 * a * T)]], dtype=float)
        return CTDiscretizeResult(G=G, H=H, Q1=Q1, M1=M1, R1=R1)


# ----------------------------
# Steady-state LQR (DARE)
# ----------------------------

@dataclass
class SSLQRResult:
    P: np.ndarray
    K: np.ndarray

class SteadyStateLQR:
    def solve(self, G: ArrayLike, H: ArrayLike, Q: ArrayLike, R: ArrayLike) -> SSLQRResult:
        G = _as_mat(G); H = _as_mat(H); Q = _as_mat(Q); R = _as_mat(R)
        P = la.solve_discrete_are(G, H, Q, R)
        K = la.inv(R + H.T @ P @ H) @ (H.T @ P @ G)
        return SSLQRResult(P=P, K=K)


# ----------------------------
# Servo LQR (integral augmentation)
# ----------------------------

@dataclass
class ServoResult:
    P: np.ndarray
    Kx: np.ndarray
    Ki: np.ndarray
    K_full: np.ndarray

class ServoLQR:
    def solve(
        self,
        G: ArrayLike,
        H: ArrayLike,
        C: ArrayLike,
        Qx: ArrayLike,
        Qi: ArrayLike,
        R: ArrayLike,
    ) -> ServoResult:
        G = _as_mat(G); H = _as_mat(H); C = _as_mat(C)
        Qx = _as_mat(Qx); Qi = _as_mat(Qi); R = _as_mat(R)
        n = G.shape[0]

        Ga = np.block([
            [ G,              np.zeros((n, 1)) ],
            [ -C @ G,         np.eye(1)        ],
        ])
        Ha = np.vstack([H, -C @ H])
        Qa = la.block_diag(Qx, Qi)

        P = la.solve_discrete_are(Ga, Ha, Qa, R)
        K_full = la.inv(R + Ha.T @ P @ Ha) @ (Ha.T @ P @ Ga)
        Kx = K_full[:, :n]
        Ki = K_full[:, n:]
        return ServoResult(P=P, Kx=Kx, Ki=Ki, K_full=K_full)


# ----------------------------
# Discrete Lyapunov analysis
# ----------------------------

@dataclass
class LyapResult:
    P: np.ndarray
    J: Optional[float]

class LyapunovAnalyzer:
    def solve(self, G: ArrayLike, Q: ArrayLike, x0: Optional[ArrayLike] = None) -> LyapResult:
        G = _as_mat(G); Q = _as_mat(Q)
        # Symmetrize Q to reduce numerical asymmetry
        Q = 0.5 * (Q + Q.T)
        try:
            P = la.solve_discrete_lyapunov(G.T, Q)
        except Exception as e:
            # Provide a clearer message while preserving the original exception
            raise RuntimeError(
                "Discrete Lyapunov solve failed. "
                "Ensure the closed-loop/state matrix is strictly stable (spectral radius < 1) "
                "and the Lyapunov operator is nonsingular."
            ) from e

        if x0 is None:
            return LyapResult(P=P, J=None)
        x0v = _as_vec(x0)
        J = float(0.5 * (x0v.T @ P @ x0v).reshape(()))
        return LyapResult(P=P, J=J)


# ----------------------------
# Parameter sweep for Lyapunov
# ----------------------------

@dataclass
class LyapunovSweepResult:
    P_star: Optional[np.ndarray]
    a_star: Optional[float]
    J_min: Optional[float]
    grid: np.ndarray
    Js: np.ndarray

class LyapunovSweep:
    def solve(
        self,
        G_template: ArrayLike,
        Q_template: ArrayLike,
        param_name: str,
        start: float,
        stop: float,
        points: int,
        x0: Optional[ArrayLike] = None,
        stability_tol: float = 1e-9,
    ) -> LyapunovSweepResult:
        """
        Sweep parameter `param_name` across [start, stop] with `points` samples.
        For each value, substitute into templates and try to solve the discrete
        Lyapunov equation G' P G - P = -Q.

        Unstable (spectral radius >= 1 - tol) or numerically unsolvable points
        are skipped and marked with cost +inf, so the CLI and app won't crash.
        """
        # Object arrays let us carry string expressions until substitution
        Gt = np.array(G_template, dtype=object, copy=True)
        Qt = np.array(Q_template, dtype=object, copy=True)

        def _substitute(M_obj: np.ndarray, pval: float) -> np.ndarray:
            return substitute_params_matrix(M_obj, {param_name: float(pval)}).astype(float, copy=False)

        def _is_stable(G: np.ndarray) -> bool:
            # strictly inside unit circle with a small tolerance
            return np.max(np.abs(np.linalg.eigvals(G))) < (1.0 - stability_tol)

        grid = np.linspace(start, stop, int(points))
        Js = np.full(grid.shape, np.inf, dtype=float)

        P_best: Optional[np.ndarray] = None
        a_star: Optional[float] = None
        J_min: Optional[float] = None

        for i, a in enumerate(grid):
            # Substitute parameter into templates
            G = _substitute(Gt, a)
            Q = _substitute(Qt, a)
            # Symmetrize Q to be safe
            Q = 0.5 * (Q + Q.T)

            # Stability gate
            if not _is_stable(G):
                continue

            # Try Lyapunov solve; treat failures as invalid points
            try:
                P = la.solve_discrete_lyapunov(G.T, Q)
            except Exception:
                continue

            # Cost
            if x0 is not None:
                x = _as_vec(x0)
                J = float(x.T @ P @ x)
            else:
                J = float(np.trace(P))

            Js[i] = J
            if (J_min is None) or (J < J_min):
                J_min = J
                a_star = float(a)
                P_best = P

        return LyapunovSweepResult(
            P_star=P_best,
            a_star=a_star,
            J_min=J_min,
            grid=grid,
            Js=Js,
        )
