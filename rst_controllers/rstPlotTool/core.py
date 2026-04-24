from __future__ import annotations
from typing import Dict, Optional, Tuple
import numpy as np

def crop_by_k(d: Dict[str, np.ndarray], kmin: Optional[float], kmax: Optional[float]) -> Dict[str, np.ndarray]:
    k = d["k"]
    mask = np.ones_like(k, dtype=bool)
    if kmin is not None:
        mask &= (k >= kmin)
    if kmax is not None:
        mask &= (k <= kmax)
    return {k_: v[mask] for k_, v in d.items()}

def robust_limits(vals: np.ndarray, robust: float) -> Tuple[float, float]:
    if vals.size == 0 or not np.isfinite(vals).any():
        return -1.0, 1.0
    if robust >= 1.0:
        lo = np.nanmin(vals); hi = np.nanmax(vals)
    else:
        qlo = (1.0 - robust) / 2.0
        qhi = 1.0 - qlo
        lo, hi = np.nanquantile(vals, [qlo, qhi])
    if not np.isfinite(lo): lo = -1.0
    if not np.isfinite(hi): hi = 1.0
    if lo == hi:
        lo -= 1.0; hi += 1.0
    return float(lo), float(hi)

def _first_crossing(x: np.ndarray, level: float):
    for i in range(1, len(x)):
        if (x[i-1] < level) and (x[i] >= level):
            return i
    return None

def step_metrics(k: np.ndarray, r: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    rf = float(r[-1])
    yf = float(y[-1])
    e = r - y
    em = float(abs(e[-1]))
    ymax = float(np.nanmax(y))
    overshoot = np.nan
    if abs(rf) > 1e-12:
        overshoot = max(0.0, (ymax - rf) / abs(rf) * 100.0)
    lo = 0.1 * rf
    hi = 0.9 * rf
    t10 = _first_crossing(y, lo) if rf >= 0 else _first_crossing(-y, -lo)
    t90 = _first_crossing(y, hi) if rf >= 0 else _first_crossing(-y, -hi)
    tr = (t90 - t10) if (t10 is not None and t90 is not None and t90 >= t10) else float("nan")
    tol = 0.02 * max(1.0, abs(rf))
    idxs = np.where(np.abs(y - rf) > tol)[0]
    tset = float("nan") if len(idxs) == 0 else float(idxs[-1] + 1)
    return dict(yf=yf, uf=float("nan"), ef=em, overshoot=overshoot, trise=tr, tsettle=tset)
