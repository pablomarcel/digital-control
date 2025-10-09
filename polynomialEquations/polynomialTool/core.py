from __future__ import annotations
from typing import List, Tuple
import numpy as np
import logging, sys
from scipy.linalg import toeplitz
from scipy.signal import dlti, dlsim

# Configure a loud logger for debugging
logger = logging.getLogger(__name__)
if not logger.handlers:
    h = logging.StreamHandler(sys.stdout)
    fmt = logging.Formatter("[%(levelname)s] %(name)s:%(lineno)d: %(message)s")
    h.setFormatter(fmt)
    logger.addHandler(h)
logger.setLevel(logging.DEBUG)

def to_asc(c_desc: List[float]) -> List[float]:
    out = list(reversed([float(x) for x in c_desc]))
    logger.debug(f"to_asc: {c_desc} -> {out}")
    return out

def to_desc(c_asc: List[float]) -> List[float]:
    out = list(reversed([float(x) for x in c_asc]))
    logger.debug(f"to_desc: {c_asc} -> {out}")
    return out

def poly_conv_desc(*polys: List[float]) -> List[float]:
    r = np.array([1.0])
    for p in polys:
        logger.debug(f"poly_conv_desc: convolving with {p}")
        r = np.convolve(r, np.asarray(p, float))
    out = r.tolist()
    logger.debug(f"poly_conv_desc: result -> {out}")
    return out

def poly_at1_desc(p: List[float]) -> float:
    val = float(np.sum(p))
    logger.debug(f"poly_at1_desc: {p} -> {val}")
    return val

def _count_trailing_zeros_desc(c: List[float], tol=1e-12) -> int:
    k, i = 0, len(c)-1
    while i>0 and abs(c[i])<=tol:
        k+=1; i-=1
    logger.debug(f"_count_trailing_zeros_desc: {c} -> k={k}")
    return k

def factor_z_from_F_and_update_d(F_desc: List[float], d: int):
    k = _count_trailing_zeros_desc(F_desc)
    if k>0:
        F_desc = F_desc[:-k]; d += k
    logger.debug(f"factor_z_from_F_and_update_d: k={k}, F'={F_desc}, d'={d}")
    return k, F_desc, d

def ogata_sylvester_E(A_desc: List[float], B_desc: List[float]):
    Aasc = to_asc(A_desc); n = len(Aasc)-1; Basc = to_asc(B_desc)
    if len(Basc) < n+1: Basc = Basc + [0.0]*(n+1-len(Basc))
    logger.debug(f"ogata_sylvester_E: n={n}, Aasc={Aasc}, Basc={Basc}")
    CA = toeplitz(Aasc + [0.0]*(n-1), [Aasc[0]] + [0.0]*(n-1))[:, :n]
    CB = toeplitz(Basc + [0.0]*(n-1), [Basc[0]] + [0.0]*(n-1))[:, :n]
    E = np.hstack([CA, CB])
    logger.debug(f"ogata_sylvester_E: E.shape={E.shape}")
    return E

def convmtx_desc(p: List[float], L: int):
    logger.debug(f"convmtx_desc: p={p}, L={L}")
    if L <= 0:
        logger.warning(f"convmtx_desc: L={L} <= 0, clamping to 1 to avoid negative dims")
        L = 1
    p = np.asarray(p, float)
    first_col = np.r_[p, np.zeros(L-1)]
    first_row = np.r_[p[0], np.zeros(L-1)]
    M = toeplitz(first_col, first_row)[:len(p)+L-1, :L]
    logger.debug(f"convmtx_desc: shape={M.shape}")
    return M

def sylvester_matrix_desc(A,B,Ls,Lr,d=0):
    logger.debug(f"sylvester_matrix_desc: A={A}, B={B}, Ls={Ls}, Lr={Lr}, d={d}")
    EA = convmtx_desc(A,Ls); EB = convmtx_desc(B,Lr)
    if d>0: 
        EB = np.r_[np.zeros((d,EB.shape[1])), EB]
        logger.debug(f"sylvester_matrix_desc: EB shifted by d={d}, new shape={EB.shape}")
    rows = max(EA.shape[0], EB.shape[0])
    EA = np.r_[EA, np.zeros((rows-EA.shape[0], EA.shape[1]))]
    EB = np.r_[EB, np.zeros((rows-EB.shape[0], EB.shape[1]))]
    E = np.hstack([EA, EB])
    logger.debug(f"sylvester_matrix_desc: E.shape={E.shape}")
    return E

def diophantine(A_desc,B_desc,D_desc,d=0,degS=None,degR=None,layout='ogata'):
    A = np.asarray(A_desc,float); B = np.asarray(B_desc,float); D = np.asarray(D_desc,float)
    logger.debug(f"diophantine: layout={layout}, A={A_desc}, B={B_desc}, D={D_desc}, d={d}, degS={degS}, degR={degR}")
    if layout=='ogata':
        n = len(A)-1; E = ogata_sylvester_E(A_desc,B_desc)
        Ddesc = list(D_desc)
        if len(Ddesc)<2*n: Ddesc += [0.0]*(2*n-len(Ddesc))
        elif len(Ddesc)>2*n: Ddesc = Ddesc[:2*n]
        Dvec = np.array(Ddesc[::-1], float)  # [d_{2n-1},...,d0]^T
        logger.debug(f"diophantine(ogata): n={n}, E.shape={E.shape}, Dvec.shape={Dvec.shape}, Dvec={Dvec.tolist()}")
        x = np.linalg.solve(E, Dvec)
        alpha_desc = x[:n][::-1].tolist(); beta_desc = x[n:][::-1].tolist()
        logger.debug(f"diophantine(ogata): alpha={alpha_desc}, beta={beta_desc}")
        return alpha_desc, beta_desc, E
    n = len(A)-1; m = len(B)-1
    if degR is None: degR = max(0, n-1)
    if degS is None: degS = max(0, m + d - 1)
    Ls,Lr = degS+1, degR+1
    logger.debug(f"diophantine(desc): n={n}, m={m}, degS={degS}, degR={degR}, Ls={Ls}, Lr={Lr}")
    E = sylvester_matrix_desc(A_desc,B_desc,Ls,Lr,d)
    rows, cols = E.shape; rows_needed = max(rows, len(D))
    if rows_needed>rows:
        E = np.vstack([E, np.zeros((rows_needed-rows, cols))]); rows = rows_needed
        logger.debug(f"diophantine(desc): padded E to rows={rows}")
    rhs = np.r_[D, np.zeros(rows - len(D))]
    logger.debug(f"diophantine(desc): rows={rows}, cols={cols}, rhs.shape={rhs.shape}, rhs[:10]={rhs[:10].tolist()}")
    x = np.linalg.solve(E, rhs) if rows==cols else np.linalg.lstsq(E, rhs, rcond=None)[0]
    S = x[:Ls]; R = x[Ls:]
    logger.debug(f"diophantine(desc): solution shapes -> S={S.shape}, R={R.shape}")
    return S.tolist(), R.tolist(), E

def dlsim_safe(sys: dlti, u, t):
    logger.debug(f"dlsim_safe: u.shape={np.shape(u)}, t.shape={np.shape(t)}")
    res = dlsim(sys,u,t=t)
    if isinstance(res, tuple) and len(res)==3: 
        logger.debug("dlsim_safe: three-tuple return detected")
        return res[0], res[1]
    if isinstance(res, tuple) and len(res)==2:
        logger.debug("dlsim_safe: two-tuple return detected")
        return res
    logger.debug("dlsim_safe: fallback return shape")
    return res[0], res[1]
