
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any

import numpy as np
import sympy as sp
from sympy.core.relational import Relational, StrictGreaterThan, StrictLessThan

from .utils import sstr, fmt_row, fmt_vec, banner

@dataclass
class Tolerances:
    abs_tol: float = 1e-10
    rel_tol: float = 1e-9
    unit_tol: float = 2e-6

def _num(x: sp.Expr) -> Optional[float]:
    try:
        if isinstance(x, (int, float)):
            return float(x)
        if isinstance(x, sp.Number):
            return float(x)
        if isinstance(x, sp.Basic) and not x.free_symbols:
            return float(sp.N(x))
    except Exception:
        pass
    return None

def _tol_for(tols: Tolerances, *vals: float) -> float:
    m = max([1.0] + [abs(v) for v in vals])
    return max(tols.abs_tol, tols.rel_tol * m)

def _cmp_vals_with_tol(tols: Tolerances, lv: float, rv: float) -> str:
    tol = _tol_for(tols, lv, rv)
    diff = lv - rv
    if abs(diff) <= tol:
        return '='
    return '>' if diff > 0 else '<'

# -------------------- Jury --------------------

def build_next_layer(v_fwd: List[sp.Expr]) -> List[sp.Expr]:
    m = len(v_fwd) - 1
    v0 = v_fwd[0]
    vm = v_fwd[-1]
    w = []
    for k in range(m):
        w_k = sp.simplify(vm * v_fwd[k+1] - v0 * v_fwd[m-1-k])
        w.append(w_k)
    return w

def jury_table_vectors(a_fwd: List[sp.Expr]) -> List[Tuple[str, List[sp.Expr], List[sp.Expr]]]:
    rows = []
    tag = 'a'
    v = list(a_fwd)
    rows.append((tag, list(reversed(v)), list(v)))
    while len(v) > 2:
        w = build_next_layer(v)
        tag = chr(ord(tag)+1)
        rows.append((tag, list(reversed(w)), list(w)))
        v = w
    return rows

def jury_inequalities(P: sp.Expr, a_fwd: List[sp.Expr], z: sp.Symbol) -> Tuple[List[Relational], List[str]]:
    n = len(a_fwd) - 1
    a0, an = a_fwd[0], a_fwd[-1]
    ineqs: List[Relational] = []
    labels: List[str] = []

    ineqs.append(StrictGreaterThan(a0, 0, evaluate=False)); labels.append("J0: a0 > 0")
    ineqs.append(StrictLessThan(sp.simplify(an**2), sp.simplify(a0**2), evaluate=False)); labels.append("J1: |a_n| < a0")
    ineqs.append(StrictGreaterThan(sp.simplify(sp.expand(P.subs(z, 1))), 0, evaluate=False)); labels.append("J2: P(1) > 0")
    sgn = 1 if (n % 2 == 0) else -1
    ineqs.append(StrictGreaterThan(sp.simplify(sgn * sp.expand(P.subs(z, -1))), 0, evaluate=False)); labels.append(f"J3: {'P(-1) > 0' if sgn==1 else 'P(-1) < 0'}")

    v = a_fwd
    layer = 1
    while len(v) > 2:
        w = build_next_layer(v)
        ineqs.append(StrictGreaterThan(sp.simplify(w[-1]**2), sp.simplify(w[0]**2), evaluate=False))
        row_len = len(w)
        letter = chr(ord('a')+layer)
        labels.append(f"J{3+layer}: |{letter}_0| > |{letter}_{row_len-1}|")
        v = w
        layer += 1

    return ineqs, labels

# -------------------- Schur–Cohn --------------------

def schur_reflection_coeffs(a_fwd: List[sp.Expr]):
    v = [sp.simplify(x) for x in a_fwd]
    kappas: List[sp.Expr] = []
    polys: List[List[sp.Expr]] = [list(v)]
    while len(v) > 1:
        a0 = v[0]; an = v[-1]
        kappa = sp.simplify(an / a0) if a0 != 0 else sp.S.ComplexInfinity
        kappas.append(kappa)
        L = len(v)
        denom = sp.simplify(1 - kappa**2)
        w: List[sp.Expr] = []
        for k in range(L-1):
            num = sp.simplify(v[k+1] - kappa * v[L-2-k])
            w.append(sp.simplify(sp.together(num / denom)))
        if w and not sp.simplify(w[0] - 1) == 0 and w[0] != 0:
            w = [sp.simplify(t / w[0]) for t in w]
        v = w
        polys.append(list(v))
        if len(v) == 1:
            break
    if not polys or not polys[-1]:
        polys.append([sp.Integer(1), sp.Integer(0)])
    return kappas, polys

def schur_inequalities(P: sp.Expr, a_fwd: List[sp.Expr], z: sp.Symbol):
    ineqs: List[Relational] = []
    labels: List[str] = []
    a0 = a_fwd[0]
    n = len(a_fwd) - 1
    ineqs.append(StrictGreaterThan(a0, 0, evaluate=False)); labels.append("S0: a0 > 0")
    ineqs.append(StrictGreaterThan(sp.simplify(sp.expand(P.subs(z, 1))), 0, evaluate=False)); labels.append("S+: P(1) > 0")
    sgn = 1 if (n % 2 == 0) else -1
    ineqs.append(StrictGreaterThan(sp.simplify(sgn * sp.expand(P.subs(z, -1))), 0, evaluate=False)); labels.append(f"S-: {'P(-1) > 0' if sgn==1 else 'P(-1) < 0'}")
    kappas, _ = schur_reflection_coeffs(a_fwd)
    for i, kappa in enumerate(kappas):
        ineqs.append(StrictLessThan(sp.simplify(kappa**2), 1, evaluate=False))
        labels.append(f"S{i+1}: |κ_{i}| < 1")
    return ineqs, labels, kappas

# -------------------- Bilinear–Routh --------------------

def bilinear_Q_from_coeffs(a_fwd: List[sp.Expr], w: sp.Symbol) -> sp.Expr:
    n = len(a_fwd) - 1
    Q = sp.Integer(0)
    for k, ak in enumerate(a_fwd):
        Q += sp.expand(sp.simplify(ak) * (1+w)**(n-k) * (1-w)**k)
    return sp.expand(Q)

def poly_coeffs_desc(poly: sp.Expr, var: sp.Symbol) -> List[sp.Expr]:
    poly = sp.expand(poly)
    P = sp.Poly(poly, var)
    return [sp.expand(c) for c in P.all_coeffs()]

def routh_array(coeffs_desc: List[sp.Expr]) -> List[List[sp.Expr]]:
    b = coeffs_desc
    n = len(b) - 1
    row1 = [sp.simplify(b[i]) for i in range(0, n+1, 2)]
    row2 = [sp.simplify(b[i]) for i in range(1, n+1, 2)]
    while len(row2) < len(row1):
        row2.append(sp.Integer(0))
    arr = [row1, row2]
    for i in range(2, n+1):
        prev = arr[i-1]
        prev2 = arr[i-2]
        denom = prev[0]
        if _num(denom) is not None:
            if abs(float(sp.N(denom))) <= max(1e-12, 1e-9 * abs(float(sp.N(denom)))):
                denom = sp.Symbol('eps', real=True, positive=True)
        newrow = []
        for j in range(len(prev2)-1):
            num = sp.simplify(prev[0]*prev2[j+1] - prev2[0]*prev[j+1])
            newrow.append(sp.simplify(sp.together(num/denom)))
        while len(newrow) < len(arr[0]):
            newrow.append(sp.Integer(0))
        arr.append(newrow)
    return arr

def routh_first_column_inequalities(arr: List[List[sp.Expr]]):
    ineqs: List[Relational] = []
    labels: List[str] = []
    for i, row in enumerate(arr):
        ineqs.append(StrictGreaterThan(sp.simplify(row[0]), 0, evaluate=False))
        labels.append(f"R{i}: first-column[{i}] > 0")
    return ineqs, labels

# -------------------- evaluation helpers --------------------

def _eval_relational_with_tol(rel, subs: Optional[Dict[sp.Symbol,float]], tols: Tolerances):
    if rel is True or rel is sp.true:
        return "True", True, False
    if rel is False or rel is sp.false:
        return "False", False, False
    if not isinstance(rel, Relational):
        try:
            return sstr(rel), None, None
        except Exception:
            return "<?>", None, None

    lhs = rel.lhs; rhs = rel.rhs

    if subs is not None:
        try:
            lv = _num(lhs.subs(subs))
            rv = _num(rhs.subs(subs))
            if (lv is not None) and (rv is not None):
                c = _cmp_vals_with_tol(tols, lv, rv)
                sym = '>' if isinstance(rel, StrictGreaterThan) else '<'
                if c == '=':
                    return f"{sstr(lv)} {sym} {sstr(rv)}", True, True
                ok = (c == '>') if isinstance(rel, StrictGreaterThan) else (c == '<')
                return f"{sstr(lv)} {sym} {sstr(rv)}", ok, False
        except Exception:
            pass

    try:
        both_numeric = not (lhs - rhs).free_symbols
    except Exception:
        both_numeric = False
    if both_numeric:
        lv = _num(lhs); rv = _num(rhs)
        if (lv is not None) and (rv is not None):
            c = _cmp_vals_with_tol(tols, lv, rv)
            sym = '>' if isinstance(rel, StrictGreaterThan) else '<'
            if c == '=':
                return f"{sstr(lv)} {sym} {sstr(rv)}", True, True
            ok = (c == '>') if isinstance(rel, StrictGreaterThan) else (c == '<')
            return f"{sstr(lv)} {sym} {sstr(rv)}", ok, False

    try:
        diff_expr = sp.simplify(lhs - rhs)
        if diff_expr.is_zero is True:
            return "CRITICAL (equality)", True, True
    except Exception:
        pass

    try:
        diff_expr = sp.simplify(lhs - rhs)
        if isinstance(rel, StrictGreaterThan):
            if getattr(diff_expr, "is_positive", None) is True:
                return sstr(rel), True, False
            if getattr(diff_expr, "is_negative", None) is True:
                return sstr(rel), False, False
        else:
            if getattr(diff_expr, "is_negative", None) is True:
                return sstr(rel), True, False
            if getattr(diff_expr, "is_positive", None) is True:
                return sstr(rel), False, False
    except Exception:
        pass

    return sstr(rel), None, None

def print_conditions(ineqs: List[Relational], labels: List[str], subs: Optional[Dict[sp.Symbol,float]], tols: Tolerances):
    text = "\n=== INEQUALITIES ===\n"
    all_true: Optional[bool] = True
    any_equal: Optional[bool] = False
    some_unknown = False

    for lab, ineq in zip(labels, ineqs):
        line, ok, eq = _eval_relational_with_tol(ineq, subs, tols)
        status = 'CRITICAL (≈ equality)' if eq else ('True' if ok else ('False' if ok is False else line))
        text += f"  {lab:<26} -> {line}   [{status}]\n"
        if ok is None:
            some_unknown = True
        else:
            all_true = (all_true and ok) if (all_true is not None) else ok
        if eq:
            any_equal = True

    return text, (None if some_unknown else all_true), (None if some_unknown else any_equal)

def reduce_and_solve(ineqs: List[Relational], param: Optional[sp.Symbol]) -> Optional[sp.Set]:
    if param is None:
        return None
    try:
        return sp.reduce_inequalities(ineqs, param)
    except Exception:
        solset = sp.S.Reals
        for r in ineqs:
            try:
                part = sp.solve_univariate_inequality(r, param, relational=False)
                solset = sp.Intersection(solset, sp.S(part))
            except Exception:
                pass
        return sp.simplify(solset)

def compute_roots(a_fwd: List[sp.Expr], subs: Dict[sp.Symbol,float]) -> List[complex]:
    coeffs_eval = [complex(sp.N(c.subs(subs))) for c in a_fwd]
    return [complex(r) for r in np.roots(np.array(coeffs_eval, dtype=complex))]

def any_radius_on_unit_circle(radii: List[float], tols: Tolerances) -> bool:
    for r in radii:
        if abs(r - 1.0) <= tols.unit_tol:
            return True
    return False

def verdict_from(all_true: Optional[bool], any_equal: Optional[bool]) -> Optional[str]:
    if all_true is None:
        return None
    if not all_true:
        return "UNSTABLE"
    if any_equal:
        return "CRITICAL (boundary)"
    return "STABLE"
