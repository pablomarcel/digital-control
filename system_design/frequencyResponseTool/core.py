# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

import numpy as np
import scipy.signal as sig

from .apis import LeadParams, LagParams, LagLeadParams
from .utils import poly_mul_desc

# ---------- small helpers ----------

def _to_float_list(x: Iterable[float]) -> List[float]:
    return [float(v) for v in x]

def _poly_pow_asc(c: np.ndarray, n: int) -> np.ndarray:
    out = np.array([1.0])
    for _ in range(n):
        out = np.polynomial.polynomial.polymul(out, c)
    return out

# ---------- z -> w bilinear mapping for G(z) (descending z powers -> ascending w powers) ----------

def z_to_w(num_desc: List[float], den_desc: List[float], T: float) -> Tuple[np.ndarray, np.ndarray]:
    a = T/2.0
    N = np.array([1.0, a])     # 1 + a w
    D = np.array([1.0, -a])    # 1 - a w

    b = list(num_desc)     # descending z
    acoef = list(den_desc) # descending z
    n = len(b) - 1
    m = len(acoef) - 1

    Num = np.array([0.0])
    for i, bi in enumerate(b):
        Num = np.polynomial.polynomial.polyadd(Num, bi * _poly_pow_asc(N, n-i) * _poly_pow_asc(D, i))

    Den = np.array([0.0])
    for i, ai in enumerate(acoef):
        Den = np.polynomial.polynomial.polyadd(Den, ai * _poly_pow_asc(N, m-i) * _poly_pow_asc(D, i))

    if m >= n:
        Num = np.polynomial.polynomial.polymul(Num, _poly_pow_asc(D, m-n))
    else:
        Den = np.polynomial.polynomial.polymul(Den, _poly_pow_asc(N, n-m))

    if Den[-1] != 0:
        k = Den[-1]
        Num = Num / k
        Den = Den / k

    return Num.astype(float), Den.astype(float)

# ---------- compensators in w (ascending in w) ----------

@dataclass(frozen=True)
class Lead:
    K: float
    alpha: float  # 0<α<1
    tau: float

    def to_w(self) -> tuple[np.ndarray, np.ndarray]:
        return np.array([self.K, self.K*self.tau], dtype=float), np.array([1.0, self.alpha*self.tau], dtype=float)

@dataclass(frozen=True)
class Lag:
    K: float
    beta: float   # β>1
    tau: float

    def to_w(self) -> tuple[np.ndarray, np.ndarray]:
        return np.array([self.K, self.K*self.tau], dtype=float), np.array([1.0, self.beta*self.tau], dtype=float)

@dataclass(frozen=True)
class LagLead:
    K: float
    beta: float
    tau_lag: float
    alpha: float
    tau_lead: float

    def to_w(self) -> tuple[np.ndarray, np.ndarray]:
        n1,d1 = Lag(self.K, self.beta, self.tau_lag).to_w()
        n2,d2 = Lead(1.0, self.alpha, self.tau_lead).to_w()
        return np.polynomial.polynomial.polymul(n1, n2), np.polynomial.polynomial.polymul(d1, d2)

# ---------- map Gd(w) -> normalized Gd(z) (descending z powers) ----------

def lead_w_to_z(p: Lead, T: float) -> tuple[list[float], list[float]]:
    g1 = 1.0 + 2.0*p.tau/T
    g0 = 1.0 - 2.0*p.tau/T
    h1 = 1.0 + 2.0*p.alpha*p.tau/T
    h0 = 1.0 - 2.0*p.alpha*p.tau/T
    num = [p.K*g1/h1, p.K*g0/h1]
    den = [1.0, h0/h1]
    return _to_float_list(num), _to_float_list(den)

def lag_w_to_z(p: Lag, T: float) -> tuple[list[float], list[float]]:
    g1 = 1.0 + 2.0*p.tau/T
    g0 = 1.0 - 2.0*p.tau/T
    h1 = 1.0 + 2.0*p.beta*p.tau/T
    h0 = 1.0 - 2.0*p.beta*p.tau/T
    num = [p.K*g1/h1, p.K*g0/h1]
    den = [1.0, h0/h1]
    return _to_float_list(num), _to_float_list(den)

def laglead_w_to_z(p: LagLead, T: float) -> tuple[list[float], list[float]]:
    nL, dL = lag_w_to_z(Lag(p.K, p.beta, p.tau_lag), T)
    nA, dA = lead_w_to_z(Lead(1.0, p.alpha, p.tau_lead), T)
    n = np.polynomial.polynomial.polymul(list(reversed(nL)), list(reversed(nA)))
    d = np.polynomial.polynomial.polymul(list(reversed(dL)), list(reversed(dA)))
    n = list(reversed(n)); d = list(reversed(d))
    k = d[0]
    n = [float(v/k) for v in n]; d = [float(v/k) for v in d]
    return n, d

# ---------- series/closed-loop in z (descending powers) ----------

def series_desc(num1: List[float], den1: List[float], num2: List[float], den2: List[float]) -> tuple[list[float], list[float]]:
    return poly_mul_desc(num1, num2), poly_mul_desc(den1, den2)

def closed_loop_desc(num_ol: List[float], den_ol: List[float]) -> tuple[list[float], list[float]]:
    n = np.array(num_ol, dtype=float); d = np.array(den_ol, dtype=float)
    if len(d) < len(n): d = np.pad(d, (len(n)-len(d), 0))
    if len(n) < len(d): n = np.pad(n, (len(d)-len(n), 0))
    return list(n), list(n + d)

# ---------- step response ----------

def step_response_csv(num_desc: List[float], den_desc: List[float], T: float, N: int, out_csv: str):
    num_asc = list(reversed(num_desc)); den_asc = list(reversed(den_desc))
    sys = sig.dlti(num_asc, den_asc, dt=T)
    t, y = sig.dstep(sys, n=N)
    k = np.arange(len(y[0]))
    data = np.column_stack([k, t.flatten(), y[0].flatten()])
    np.savetxt(out_csv, data, delimiter=",", header="k,t,c(k)", comments="", fmt="%.10g")

# ---------- auto-lead heuristic ----------

def estimate_Kv(num_asc: np.ndarray, den_asc: np.ndarray, nu_small: np.ndarray) -> float:
    jw = 1j*nu_small
    H = eval_rational_asc(num_asc, den_asc, jw)
    return float(np.median(nu_small*np.abs(H)))

def eval_rational_asc(num_asc: np.ndarray, den_asc: np.ndarray, jw: np.ndarray) -> np.ndarray:
    num = np.zeros_like(jw, dtype=complex)
    den = np.zeros_like(jw, dtype=complex)
    pw  = np.ones_like(jw, dtype=complex)
    for c in num_asc:
        num += c * pw
        pw *= jw
    pw  = np.ones_like(jw, dtype=complex)
    for c in den_asc:
        den += c * pw
        pw *= jw
    return num/den

def auto_lead(Gw_num: np.ndarray, Gw_den: np.ndarray, T: float,
              pm_req: float, gm_req: float, Kv_req: float) -> Lead:
    from .design import make_nu_grid, bode_from_asc
    nu = make_nu_grid(T)
    Kv_base = estimate_Kv(Gw_num, Gw_den, nu[:max(8, len(nu)//100)])
    K0 = Kv_req / Kv_base if Kv_base > 0 else 1.0
    mag0, ph0 = bode_from_asc(K0*Gw_num, Gw_den, nu)

    def _x_at_y(x, y, y0):
        s = np.sign(y - y0); idx = np.where(np.diff(s)!=0)[0]
        if len(idx)==0: return None
        i=idx[0]; x1,x2=x[i],x[i+1]; y1,y2=y[i],y[i+1]
        t=0.0 if y2==y1 else (y0-y1)/(y2-y1); return float(x1+t*(x2-x1))

    nu_gc = _x_at_y(nu, mag0, 0.0)
    pm0 = (180.0 + float(np.interp(nu_gc, nu, ph0))) if nu_gc is not None else 0.0

    phi_add = max(0.0, pm_req - pm0 + 8.0)
    s = np.sin(np.deg2rad(phi_add))
    alpha = float(np.clip((1 - s)/(1 + s), 0.05, 0.95))
    target_db = -20*np.log10(1/np.sqrt(alpha))
    idx = int(np.argmin(np.abs(mag0 - target_db)))
    nu_c = float(nu[idx])
    tau  = 1.0/(nu_c*np.sqrt(alpha))
    return Lead(K=float(K0), alpha=alpha, tau=float(tau))
