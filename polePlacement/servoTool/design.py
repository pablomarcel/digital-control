from __future__ import annotations
from typing import List, Optional
import numpy as np

def fmt_num(val: float) -> str:
    try:
        import sympy as sp  # type: ignore
        q = sp.nsimplify(val, rational=True, maxsteps=50)
        return str(q)
    except Exception:
        return f"{val:.12g}"

def servo_eqs(G: np.ndarray, H: np.ndarray, C: np.ndarray,
              K1: np.ndarray, K2: np.ndarray) -> List[str]:
    n = int(G.shape[0])
    m = int(C.shape[0] if C.ndim == 2 else 1)
    lines: List[str] = []
    if m == 1:
        terms = []
        for j in range(n):
            c = float(K2[0, j])
            if abs(c) < 1e-15:
                continue
            coef = fmt_num(-c)
            terms.append(f"{coef}*x{j+1}(k)")
        vcoef = fmt_num(float(K1[0, 0]))
        rhs = " + ".join(([f"{vcoef}*v(k)"] + terms)) if terms else f"{vcoef}*v(k)"
        lines.append(f"u(k) = {rhs}")
    else:
        lines.append("u(k) = -K2 x(k) + K1 v(k)")
    lines.append("x(k+1) = G x(k) + H u(k)")
    lines.append("y(k)   = C x(k)")
    lines.append("v(k+1) = v(k) + r(k+1) - y(k+1)")
    return lines

def observer_eqs(mode: str = 'current', Ke_shape: Optional[tuple[int,int]] = None) -> List[str]:
    lines: List[str] = []
    lines.append("Measured-form coordinates: choose T such that C*T = [ I  0 ]")
    lines.append("x_hat(k) = T * [ y(k) ; xi_hat_b(k) ]")
    if (mode or 'current').lower() == 'current':
        lines.append("xi_hat_b(k+1) = (Gbb - Ke*Gab) xi_hat_b(k) + (Gba - Ke*Gaa) y(k) + (Hb - Ke*Ha) u(k) + Ke*y(k+1)")
    else:
        lines.append("xi_hat_b(k+1) = (Gbb - Ke*Gab) xi_hat_b(k) + (Gba - Ke*Gaa) y(k) + (Hb - Ke*Ha) u(k)")
    if Ke_shape:
        lines.append(f"[info] Ke shape = {Ke_shape}")
    return lines

def emit_equations(lines: List[str], eq_file: Optional[str], eq_stdout: bool) -> str:
    text = "\n".join(lines) + ("\n" if lines else "")
    return text
