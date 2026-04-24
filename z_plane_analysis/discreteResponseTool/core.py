
from __future__ import annotations
import numpy as np
from typing import Tuple, Optional, Dict, Sequence

try:
    import scipy.signal as sig
except Exception:
    sig = None  # pragma: no cover

def poly_conv_q(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.convolve(a, b)

def poly_add_q(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    n = max(len(a), len(b))
    out = np.zeros(n)
    out[:len(a)] += a
    out[:len(b)] += b
    return out

def _count_trailing_zeros_desc(v: np.ndarray, tol: float = 1e-14) -> int:
    n = 0
    for x in v[::-1]:
        if abs(x) <= tol: n += 1
        else: break
    return n

def zpoly_from_q(qcoef: np.ndarray, m: int) -> np.ndarray:
    p = np.asarray(qcoef, dtype=float)
    out = np.zeros(m + 1, dtype=float)
    out[:len(p)] = p
    return out

def roots_from_desc(cdesc: np.ndarray) -> np.ndarray:
    tz = _count_trailing_zeros_desc(cdesc)
    base = cdesc[:len(cdesc)-tz] if (len(cdesc)-tz) > 0 else np.array([])
    roots = np.roots(base) if base.size > 1 else (np.array([]) if base.size == 0 else np.array([]))
    if tz > 0:
        roots = np.concatenate([roots, np.zeros(tz)])
    return roots

def zroots_from_q(qcoef: np.ndarray) -> np.ndarray:
    deg = max(0, len(qcoef) - 1)
    cdesc = zpoly_from_q(qcoef, deg)
    return roots_from_desc(cdesc)

def poly_eval_q_at1(p: np.ndarray) -> float:
    return float(np.sum(np.asarray(p, dtype=float)))

def cont2disc_zoh(num_s: Sequence[float], den_s: Sequence[float], T: float) -> Tuple[np.ndarray, np.ndarray]:
    if sig is None:
        raise RuntimeError("scipy is required (pip install scipy)")
    sysc = sig.TransferFunction(num_s, den_s)
    numz, denz, _ = sig.cont2discrete((sysc.num, sysc.den), T, method='zoh')[:3]
    bq = np.squeeze(np.array(numz, dtype=float))
    aq = np.squeeze(np.array(denz, dtype=float))
    if abs(aq[0]-1.0) > 1e-14:
        bq /= aq[0]; aq /= aq[0]
    return bq, aq

def pid_positional_q(Kp: float, Ki: float, Kd: float) -> Tuple[np.ndarray, np.ndarray]:
    b0 = Ki + Kp + Kd
    b1 = -(Kp + 2*Kd)
    b2 = Kd
    bq = np.array([b0, b1, b2], dtype=float)
    aq = np.array([1.0, -1.0], dtype=float)
    return bq, aq

def analog_pid_to_positional_q(K: float, Ti: float, Td: float, T: float) -> Tuple[np.ndarray, np.ndarray]:
    Kp = K - (K*T)/(2*Ti) if Ti != 0 else K
    Ki = (K*T)/Ti if Ti != 0 else 0.0
    Kd = (K*Td)/T if T != 0 else 0.0
    return pid_positional_q(Kp, Ki, Kd)

def make_controller_from_kwargs(**kwargs) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], str]:
    if kwargs.get("ctrl_numz") is not None and kwargs.get("ctrl_denz") is not None:
        import numpy as np
        return np.array(kwargs["ctrl_numz"], float), np.array(kwargs["ctrl_denz"], float), "Digital (direct)"
    if any(kwargs.get(k) is not None for k in ("Kp","Ki","Kd")):
        bq, aq = pid_positional_q(float(kwargs.get("Kp") or 0.0),
                                  float(kwargs.get("Ki") or 0.0),
                                  float(kwargs.get("Kd") or 0.0))
        return bq, aq, "Digital PID (positional)"
    if any(kwargs.get(k) is not None for k in ("K","Ti","Td")):
        T = float(kwargs["T"])
        bq, aq = analog_pid_to_positional_q(float(kwargs.get("K") or 0.0),
                                            float(kwargs.get("Ti") or 1e9),
                                            float(kwargs.get("Td") or 0.0),
                                            T)
        return bq, aq, "Analog PID → Digital positional"
    return None, None, ""

def series_q(num1: np.ndarray, den1: np.ndarray, num2: np.ndarray, den2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    return poly_conv_q(num1, num2), poly_conv_q(den1, den2)

def feedback_cl_q(numL: np.ndarray, denL: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    n = max(len(numL), len(denL))
    Np = np.zeros(n); Dp = np.zeros(n)
    Np[:len(numL)] = numL
    Dp[:len(denL)] = denL
    denom = Dp + Np
    num = Np.copy()
    if abs(denom[0]) > 0:
        num /= denom[0]; denom /= denom[0]
    return num, denom

def filt_lti_q(bq: np.ndarray, aq: np.ndarray, x: np.ndarray) -> np.ndarray:
    N = int(len(x))
    y = np.zeros(N, dtype=float)
    for k in range(N):
        acc = 0.0
        for i in range(len(bq)):
            if k - i >= 0: acc += bq[i] * x[k - i]
        for j in range(1, len(aq)):
            if k - j >= 0: acc -= aq[j] * y[k - j]
        y[k] = acc / aq[0]
    return y

def step_metrics(y: np.ndarray, tol: float = 0.02) -> Dict[str, Optional[float]]:
    if y.size == 0 or not np.all(np.isfinite(y)):
        return {"final": None, "peak": None, "k_peak": None, "overshoot_pct": None, "k_rise_90pct": None, "k_settle": None}
    final = float(y[-1])
    peak = float(np.max(y)); k_peak = int(np.argmax(y))
    overshoot = float(max(0.0, (peak - final) / (abs(final) if final else 1.0) * 100.0))
    target = 0.9 * final
    same_sign = (np.sign(y) == np.sign(final)) if final != 0 else np.ones_like(y, bool)
    idx = np.where(same_sign & (np.abs(y) >= abs(target)))[0]
    k_rise = int(idx[0]) if idx.size else None
    band = tol * abs(final) if final != 0 else tol
    k_settle = None
    for k in range(len(y)):
        if np.all(np.abs(y[k:] - final) <= band):
            k_settle = k; break
    return {"final": final, "peak": peak, "k_peak": k_peak,
            "overshoot_pct": overshoot, "k_rise_90pct": k_rise, "k_settle": k_settle}

def diophantine_place(Np: np.ndarray, Dp: np.ndarray, A_des: np.ndarray):
    nD = len(Dp)-1
    nN = len(Np)-1
    deg_Ad = max(0, nD)
    deg_Bd = max(0, (len(A_des)-1) - nN)
    n_va = deg_Ad
    L = len(A_des)

    def pad_right(p, L):
        out = np.zeros(L); out[:min(L,len(p))] = p[:min(L,len(p))]; return out

    base = pad_right(Dp, L)
    Acols = [pad_right(np.pad(Dp, (i,0)), L) for i in range(1, deg_Ad+1)]
    Acols = np.column_stack(Acols) if Acols else np.zeros((L,0))
    Bcols = [pad_right(np.pad(Np, (j,0)), L) for j in range(deg_Bd+1)]
    Bcols = np.column_stack(Bcols) if Bcols else np.zeros((L,0))

    M = np.column_stack([Acols, Bcols]) if (Acols.size or Bcols.size) else np.zeros((L,0))
    rhs = A_des - base
    if M.size == 0:
        a = np.zeros(0); b = np.zeros(0)
    else:
        sol, *_ = np.linalg.lstsq(M, rhs, rcond=None)
        a = sol[:n_va]; b = sol[n_va:]
    Ad = np.concatenate(([1.0], a)) if n_va>0 else np.array([1.0])
    Bd = b if (deg_Bd+1)>0 else np.array([0.0])
    return Bd, Ad
