from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Literal
import numpy as np

NoiseMode = Literal["state", "input"]

@dataclass
class KalmanModel:
    A: np.ndarray
    B: np.ndarray
    C: np.ndarray
    G: np.ndarray
    Q_state: Optional[np.ndarray]
    Qw: Optional[np.ndarray]
    R: np.ndarray
    noise_mode: NoiseMode

    @property
    def n(self) -> int:
        return self.A.shape[0]
    @property
    def p(self) -> int:
        return self.C.shape[0]
    def GQGT(self) -> np.ndarray:
        if self.noise_mode == "state":
            assert self.Q_state is not None
            return self.Q_state
        assert self.Qw is not None
        return self.G @ self.Qw @ self.G.T

def coerce_shapes(A, B, C, G, Q, R, dt, q_scalar: float | None, Q_arg_was_none: bool) -> KalmanModel:
    n = A.shape[0]
    if C.ndim == 1:
        C = C.reshape(1, -1)
    assert C.shape[1] == n, f"C must have {n} columns (got {C.shape})"
    p = C.shape[0]
    if B.ndim == 1:
        B = B.reshape(-1, 1)
    assert B.shape[0] == n, f"B must have {n} rows (got {B.shape})"
    # R coercion
    if np.ndim(R) == 0:
        R = np.array([[float(R)]])
    if R.shape == (1, 1) and p > 1:
        R = np.eye(p) * float(R[0, 0])
    if R.shape == (p,):
        R = R.reshape(p, 1)
    if R.shape == (p, 1):
        R = np.diagflat(R)
    assert R.shape == (p, p), f"R must be {p}x{p} (got {R.shape})"
    # G
    if G is not None and G.shape[0] != n and G.shape[1] == n:
        G = G.T
    if G is None:
        G = np.zeros((n, 0))
    assert G.shape[0] == n, f"G must have {n} rows (got {G.shape})"
    # Q interpretation
    Q_state: Optional[np.ndarray] = None
    Qw: Optional[np.ndarray] = None
    noise_mode: NoiseMode = "state"
    if Q_arg_was_none:
        Q_state = Q
        noise_mode = "state"
    else:
        if np.ndim(Q) == 0:
            if G.shape[1] > 0:
                Qw = float(Q) * np.eye(G.shape[1])
                noise_mode = "input"
            else:
                Q_state = float(Q) * np.eye(n)
                noise_mode = "state"
        elif Q.shape == (n, n):
            Q_state = Q
            noise_mode = "state"
        elif G.shape[1] > 0 and Q.shape == (G.shape[1], G.shape[1]):
            Qw = Q
            noise_mode = "input"
        else:
            raise ValueError(f"Cannot interpret Q with shapes Q={Q.shape}, G={G.shape}, A={A.shape}")
    return KalmanModel(A=A, B=B, C=C, G=G, Q_state=Q_state, Qw=Qw, R=R, noise_mode=noise_mode)

def default_cv_model(dt: float, q: float, r: float):
    A = np.array([[1.0, dt],[0.0, 1.0]], float)
    B = np.array([[0.5*dt**2],[dt]], float)
    C = np.array([[1.0, 0.0]], float)
    G = np.array([[0.5*dt**2],[dt]], float)
    Q_state = q * np.array([[dt**4/4, dt**3/2],
                            [dt**3/2, dt**2 ]], float)
    R = np.array([[r]], float)
    return A,B,C,G,Q_state,R

def dare_estimation(A: np.ndarray, C: np.ndarray, GQGT: np.ndarray, R: np.ndarray) -> np.ndarray:
    try:
        from scipy.linalg import solve_discrete_are
        P = solve_discrete_are(A.T, C.T, GQGT, R)
        return P
    except Exception:
        P = np.eye(A.shape[0])
        for _ in range(10000):
            S = C @ P @ C.T + R
            Pn = A @ P @ A.T - A @ P @ C.T @ np.linalg.inv(S) @ C @ P @ A.T + GQGT
            if np.linalg.norm(Pn - P, ord='fro') < 1e-10:
                P = Pn
                break
            P = Pn
        return P

from dataclasses import dataclass

@dataclass
class SimulationResult:
    t: np.ndarray
    X_true: np.ndarray
    X_hat: np.ndarray
    Y_meas: np.ndarray
    K_gain: Optional[np.ndarray]
    meta: dict

class Simulator:
    def __init__(self, model: KalmanModel, dt: float, T: float, seed: int = 1, steady: bool = False, u: float = 0.0):
        self.model = model
        self.dt = dt
        self.T = T
        self.seed = seed
        self.steady = steady
        self.u = u

    def run(self, x0: np.ndarray, P0: np.ndarray, xtrue0: np.ndarray) -> SimulationResult:
        A,B,C = self.model.A, self.model.B, self.model.C
        n, p = self.model.n, self.model.p
        rng = np.random.default_rng(self.seed)
        N = int(np.round(self.T / self.dt)) + 1
        Tvec = np.linspace(0.0, self.T, N)
        X_true = np.zeros((n, N))
        X_hat  = np.zeros((n, N))
        Y_meas = np.zeros((p, N))
        xh = x0.reshape(n,1)
        P  = P0.copy()
        x  = xtrue0.reshape(n,1)
        Kss = None
        if self.steady:
            GQGT = self.model.GQGT()
            Pss = dare_estimation(A, C, GQGT, self.model.R)
            Sss = C @ Pss @ C.T + self.model.R
            Kss = Pss @ C.T @ np.linalg.inv(Sss)
        for k in range(N):
            X_true[:,k:k+1] = x
            X_hat[:,k:k+1]  = xh
            v_meas = rng.multivariate_normal(np.zeros(p), self.model.R).reshape(p,1)
            y = C @ x + v_meas
            Y_meas[:,k:k+1] = y
            if self.steady:
                K = Kss
                nu = y - C @ xh
                xh = xh + K @ nu
                P = (np.eye(n) - K @ C) @ P
            else:
                ucol = np.full((B.shape[1], 1), self.u, dtype=float)
                xh_pred = A @ xh + B @ ucol
                P_pred  = A @ P @ A.T + self.model.GQGT()
                S = C @ P_pred @ C.T + self.model.R
                K = P_pred @ C.T @ np.linalg.inv(S)
                nu = y - C @ xh_pred
                xh = xh_pred + K @ nu
                I = np.eye(n)
                P = (I - K @ C) @ P_pred @ (I - K @ C).T + K @ self.model.R @ K.T
            ucol = np.full((B.shape[1], 1), self.u, dtype=float)
            if self.model.noise_mode == "state":
                v = rng.multivariate_normal(np.zeros(n), self.model.Q_state).reshape(n,1)  # type: ignore
                x = A @ x + B @ ucol + v
            else:
                m = self.model.G.shape[1]
                w = rng.multivariate_normal(np.zeros(m), self.model.Qw).reshape(m,1)  # type: ignore
                x = A @ x + B @ ucol + self.model.G @ w
        meta = {
            "A": A.tolist(), "B": B.tolist(), "C": C.tolist(), "G": self.model.G.tolist(),
            "Q_state": (None if self.model.Q_state is None else self.model.Q_state.tolist()),
            "Qw": (None if self.model.Qw is None else self.model.Qw.tolist()),
            "R": self.model.R.tolist(), "dt": self.dt, "T": self.T,
            "steady": bool(self.steady), "noise_mode": self.model.noise_mode
        }
        return SimulationResult(t=Tvec, X_true=X_true, X_hat=X_hat, Y_meas=Y_meas, K_gain=K, meta=meta)  # type: ignore
