
from __future__ import annotations
from typing import List, Tuple, Optional
import sympy as sp
from .utils import to_float_list, coeffs_desc_to_expr, expr_to_poly

def parse_poly(num: Optional[str], den: Optional[str], form: str,
               zeros: Optional[str], poles: Optional[str], gain: Optional[float]) -> Tuple[List[float], List[float]]:
    """
    Return (b, a) for Ogata 5-6 layout:
      H(z) = (b0 + b1 z^-1 + ... + bn z^-n) / (1 + a1 z^-1 + ... + an z^-n)
    """
    z = sp.symbols('z')

    if form == "zpk":
        z_list = to_float_list(zeros or "")
        p_list = to_float_list(poles or "")
        k = float(gain if gain is not None else 1.0)
        Nz = sp.Integer(1)
        for zk in z_list:
            Nz *= (z - sp.nsimplify(zk))
        Dz = sp.Integer(1)
        for pk in p_list:
            Dz *= (z - sp.nsimplify(pk))
        Nz = sp.simplify(k * Nz)
        return polyz_to_zmin1(Nz, Dz)

    if form == "auto":
        def looks_expr(s: Optional[str]) -> bool:
            if not s:
                return False
            s2 = s.replace(" ", "")
            return ("z" in s2) or ("**" in s2) or any(c in s2 for c in "()+-*/")
        form = "expr" if looks_expr(num) or looks_expr(den) else "zmin1"

    if form == "zmin1":
        if not (num and den):
            raise ValueError("For --form zmin1 pass --num and --den lists.")
        b = to_float_list(num)
        d = to_float_list(den)
        if not d:
            raise ValueError("Denominator list cannot be empty.")
        if abs(d[0] - 1.0) > 1e-12:
            a0 = d[0]
            d = [x / a0 for x in d]
            b = [x / a0 for x in b]
        if abs(d[0] - 1.0) > 1e-12:
            raise ValueError("Normalization failed: denominator not monic.")
        a = d[1:]
        n = len(a)
        if len(b) < n + 1:
            b = b + [0.0] * (n + 1 - len(b))
        elif len(b) > n + 1:
            b = b[:n + 1]
        return b, a

    if form == "z":
        if not (num and den):
            raise ValueError("For --form z pass --num and --den coefficient lists (descending powers).")
        num_coeffs = to_float_list(num)
        den_coeffs = to_float_list(den)
        Nz = coeffs_desc_to_expr(num_coeffs, z) if num_coeffs else sp.Integer(0)
        Dz = coeffs_desc_to_expr(den_coeffs, z)
        return polyz_to_zmin1(Nz, Dz)

    if form == "expr":
        if not (num and den):
            raise ValueError("For --form expr pass --num and --den expressions in z.")
        Nz = sp.simplify(sp.sympify(num, locals={'z': z}))
        Dz = sp.simplify(sp.sympify(den, locals={'z': z}))
        return polyz_to_zmin1(Nz, Dz)

    raise ValueError(f"Unknown --form '{form}'.")

def polyz_to_zmin1(Nz: sp.Expr, Dz: sp.Expr):
    z = sp.symbols('z')
    Dz = sp.simplify(Dz)
    Nz = sp.simplify(Nz)

    Dp = expr_to_poly(Dz, z)
    lc = sp.nsimplify(Dp.LC())
    if lc != 1:
        Dz = sp.simplify(Dz / lc)
        Nz = sp.simplify(Nz / lc)
        Dp = expr_to_poly(Dz, z)

    n = Dp.degree()
    Np = expr_to_poly(Nz, z)
    if Np.degree() >= n:
        _, r = sp.div(Np, Dp)
        Nz = r.as_expr()
        Np = expr_to_poly(Nz, z)

    den_desc = Dp.all_coeffs()
    num_desc = Np.all_coeffs()
    if len(num_desc) < n + 1:
        num_desc = [sp.Integer(0)] * (n + 1 - len(num_desc)) + num_desc

    a = [float(sp.N(c)) for c in den_desc[1:]]
    b = [float(sp.N(c)) for c in num_desc]
    return b, a
