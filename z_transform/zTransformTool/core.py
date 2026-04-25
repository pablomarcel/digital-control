#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pure computational routines for zTransformTool.

This module intentionally avoids command-line parsing and printing. It contains
symbolic and numeric helpers for forward z transforms, unilateral inverse
z transforms, finite series expansion, transfer-function utilities, and
difference-equation solving.

The inverse-z workflow is written around the substitution ``u = 1/z``. Rational
expressions are converted to ``B(u) / A(u)`` with ``A(0)`` nonzero when possible.
The finite unilateral sequence is computed from the recurrence, and the symbolic
closed form is matched back to those recurrence samples so repeated poles,
polynomial factors in ``k``, and input delays remain consistent with the
unilateral convention.
"""
from __future__ import annotations
from typing import Dict, Any, Optional, List, Tuple
import os
import logging

import numpy as np
import sympy as sp
from scipy.signal import residuez

try:
    import control as ct
except Exception:
    ct = None


# ---------- Logging setup ----------
_LOG = logging.getLogger("ztt.core")
if os.environ.get("ZTT_LOG", "").strip() not in ("", "0", "false", "False"):
    if not _LOG.handlers:
        _handler = logging.StreamHandler()
        _handler.setFormatter(logging.Formatter("[%(levelname)s] ztt.core: %(message)s"))
        _LOG.addHandler(_handler)
    _LOG.setLevel(logging.DEBUG)
else:
    _LOG.addHandler(logging.NullHandler())

_DUMP_MATS = os.environ.get("ZTT_LOG_MATRICES", "").strip() not in ("", "0", "false", "False")


def _num(expr):
    try:
        return sp.N(sp.simplify(expr))
    except Exception:
        return expr


def _floatish(x) -> float:
    """Safely convert (possibly complex, tiny-imag) SymPy to float(real)."""
    try:
        return float(complex(sp.N(sp.simplify(x))).real)
    except Exception:
        try:
            return float(sp.N(sp.re(x)))
        except Exception:
            return float(sp.N(x))


# ---------- Substitution normalization ----------
def _normalize_subs(subs: Dict, syms: Dict[str, sp.Symbol]) -> Dict:
    if not subs:
        return {}
    out = {}
    for k, v in subs.items():
        if isinstance(k, str) and k in syms:
            out[syms[k]] = v
        else:
            out[k] = v
    return out


# ---------- Internal helpers (forward closed-forms) ----------
def _is_k_mult(expr, k):
    expr = sp.simplify(expr)
    if expr.has(k):
        q = sp.simplify(expr / k)
        if not q.has(k):
            return q
    return None


def _extract_r_term(xk, k):
    # p**k
    if isinstance(xk, sp.Pow) and xk.exp == k and not xk.base.has(k):
        return xk.base
    # exp(c*k)
    if xk.func is sp.exp and xk.args:
        c = _is_k_mult(sp.simplify(xk.args[0]), k)
        if c is not None:
            return sp.exp(c)
    return None


def _match_trig(xk, k):
    xk = sp.simplify(xk)
    # r^k * trig(Ωk)
    if isinstance(xk, sp.Mul):
        r, trig = None, None
        for fac in sp.Mul.make_args(xk):
            rr = _extract_r_term(fac, k)
            if rr is not None:
                r = rr if r is None else r * rr
            elif fac.func in (sp.sin, sp.cos):
                trig = fac
        if trig is not None:
            omega = _is_k_mult(trig.args[0], k)
            if omega is not None:
                return (trig.func.__name__, r if r is not None else sp.Integer(1), sp.simplify(omega))
    # pure trig
    if xk.func in (sp.sin, sp.cos):
        omega = _is_k_mult(xk.args[0], k)
        if omega is not None:
            return (xk.func.__name__, sp.Integer(1), sp.simplify(omega))
    return None


def forward_z_closed_form(xk, z, k):
    """
    Ogata-style pairs:
      1 -> z/(z-1)
      r^k -> z/(z-r)
      sin(Ωk) -> z*sinΩ / (z^2 - 2z cosΩ + 1)
      cos(Ωk) -> z(z - cosΩ) / (z^2 - 2z cosΩ + 1)
      r^k sin(Ωk) -> z r sinΩ / (z^2 - 2 r z cosΩ + r**2)
      r^k cos(Ωk) -> z (z - r cosΩ) / (z^2 - 2 r z cosΩ + r**2)
    """
    xk = sp.simplify(xk)

    if xk == 1:
        return sp.simplify(z / (z - 1))

    r0 = _extract_r_term(xk, k)
    if r0 is not None:
        return sp.simplify(z / (z - r0))

    mt = _match_trig(xk, k)
    if mt is not None:
        kind, r, Om = mt
        den = (z**2 - 2*z*sp.cos(Om) + 1) if r == 1 else (z**2 - 2*r*z*sp.cos(Om) + r**2)
        if kind == 'sin':
            num = z*(sp.sin(Om) if r == 1 else r*sp.sin(Om))
        else:
            num = z*((z - sp.cos(Om)) if r == 1 else (z - r*sp.cos(Om)))
        return sp.simplify(num/den)

    # linear combos of known pairs
    if isinstance(xk, sp.Add):
        parts = [forward_z_closed_form(t, z, k) for t in sp.Add.make_args(xk)]
        if all(p is not None for p in parts):
            return sp.simplify(sum(parts))

    # separable multiplicative constant
    if isinstance(xk, sp.Mul):
        coeff = sp.Integer(1)
        core  = sp.Integer(1)
        for fac in sp.Mul.make_args(xk):
            if not fac.has(k):
                coeff *= fac
            else:
                core *= fac
        if core is not sp.Integer(1):
            Xc = forward_z_closed_form(core, z, k)
            if Xc is not None:
                return sp.simplify(coeff * Xc)

    return None


# ---------- Inverse-z building blocks ----------
def _min_pow_u(expr, u):
    expr = sp.expand(expr)
    mn = 0
    for term in sp.Add.make_args(expr):
        e = 0
        for fac in sp.Mul.make_args(term):
            if fac == u:
                e += 1
            elif isinstance(fac, sp.Pow) and fac.base == u and fac.exp.is_Integer:
                e += int(fac.exp)
        mn = min(mn, e)
    return mn


def Xu_from_Xz(XZ, z):
    u = sp.Symbol('u')
    Xu = sp.simplify(sp.together(XZ.subs({z: 1/u})))
    if _LOG.isEnabledFor(logging.DEBUG):
        _LOG.debug("Xu_from_Xz: XZ=%s", XZ)
        _LOG.debug("Xu_from_Xz: Xu=%s", sp.simplify(Xu))
    return u, Xu


def rational_AB_in_u(Xu, u) -> Tuple[sp.Poly, sp.Poly]:
    """
    Return polynomials A(u), B(u) with X(u) = B(u)/A(u), ensuring:
    - no negative powers of u
    - A(0) != 0 (divide out leading u factors if necessary, adjusting B too)
    """
    num, den = sp.together(Xu).as_numer_denom()
    num = sp.expand(num); den = sp.expand(den)

    # Eliminate negative powers by multiplying both by u^{-s} if needed
    s = min(_min_pow_u(num, u), _min_pow_u(den, u))
    if s < 0:
        num = sp.simplify(num * u**(-s))
        den = sp.simplify(den * u**(-s))

    B = sp.Poly(sp.expand(num), u, domain='EX')
    A = sp.Poly(sp.expand(den), u, domain='EX')

    # Drop a common u^m factor so that A(0) != 0 (pure delay removal)
    exps = [e for (e,), _ in A.as_dict().items()]
    if exps:
        m = int(min(exps))
        if m > 0:
            A = sp.Poly(sp.expand(A.as_expr() / u**m), u, domain='EX')
            B = sp.Poly(sp.expand(B.as_expr() / u**m), u, domain='EX')

    while sp.simplify(A.eval(0)) == 0:
        A = sp.Poly(sp.expand(A.as_expr() / u), u, domain='EX')
        B = sp.Poly(sp.expand(B.as_expr() / u), u, domain='EX')

    if _LOG.isEnabledFor(logging.DEBUG):
        _LOG.debug("rational_AB_in_u: A(u)=%s ; deg(A)=%d", A.as_expr(), A.degree())
        _LOG.debug("rational_AB_in_u: B(u)=%s ; deg(B)=%d", B.as_expr(), B.degree())

    return A, B


def seq_by_convolution(A: sp.Poly, B: sp.Poly, N: int) -> List[sp.Expr]:
    """Finite-length unilateral sequence from A(u) X(u) = B(u)."""
    def coeff(poly: sp.Poly, i: int):
        return poly.nth(i) if i >= 0 else sp.Integer(0)

    n = A.degree()
    A0 = coeff(A, 0)
    if sp.simplify(A0) == 0:
        raise ValueError("A(0) must be nonzero for unilateral inversion.")

    x = [sp.Integer(0)] * (N + 1)
    for k in range(N + 1):
        rhs = coeff(B, k)
        for i in range(1, min(n, k) + 1):
            rhs -= coeff(A, i) * x[k - i]
        x[k] = sp.simplify(rhs / A0)

    if _LOG.isEnabledFor(logging.DEBUG):
        _LOG.debug("seq_by_convolution: N=%d, seq[0..min(6,N)]=%s", N, [sp.simplify(s) for s in x[:min(7, len(x))]])

    return x


# ---------- Root utilities ----------
def _derivative_multiplicity(P: sp.Poly, r: sp.Symbol, rho: sp.Expr) -> int:
    """
    Compute multiplicity of root 'rho' for polynomial P by successive derivatives:
      smallest m>=1 with d^(m-1)P/dr^(m-1) at rho == 0 and d^m P/dr^m at rho != 0
    Returns at least 1 if P(rho)==0, else 0.
    """
    expr = sp.expand(P.as_expr())
    if sp.simplify(expr.subs({r: rho})) != 0:
        return 0
    m = 1
    while True:
        d = sp.diff(expr, r, m - 1)
        if sp.simplify(d.subs({r: rho})) != 0:
            # shouldn’t happen for m==1 because we checked P(rho)==0; keep safe
            return m - 1 if m > 1 else 0
        dm = sp.diff(expr, r, m)
        if sp.simplify(dm.subs({r: rho})) != 0:
            return m
        m += 1


def _roots_with_multiplicity(P: sp.Poly, r: sp.Symbol) -> Dict[sp.Expr, int]:
    """
    Return {rho: mult} for P(r). Robust to symbolic params:
      1) Try exact factor_list to gather (linear) factors + multiplicity.
      2) Also gather roots from solve() (often drops multiplicities),
         then compute multiplicities by successive derivatives.
      3) If total multiplicity < degree, and 1 is a root, assign the remainder
         to rho=1 (typical repeated pole at z=1). Otherwise add to the first root.
    """
    rho_mult: Dict[sp.Expr, int] = {}

    # 1) exact factorization for linear factors
    try:
        _, flist = sp.factor_list(P.as_expr())
    except Exception:
        flist = []
    for fac, mult in flist:
        deg = sp.degree(fac, r)
        if deg == 1:
            poly = sp.Poly(fac, r)
            a1, a0 = poly.all_coeffs()  # [a, b]
            rho = sp.simplify(-a0 / a1)
            rho_mult[sp.simplify(rho)] = max(int(mult), rho_mult.get(sp.simplify(rho), 0))

    # 2) add roots from solve() and evaluate multiplicity via derivatives
    try:
        sols = sp.solve(sp.Eq(P.as_expr(), 0), r)
    except Exception:
        sols = []
    for s in sols:
        rho = sp.simplify(s)
        m = _derivative_multiplicity(P, r, rho)
        if m > 0:
            rho_mult[rho] = max(m, rho_mult.get(rho, 0))

    # Ensure we account for full degree
    deg = P.degree()
    total_m = sum(rho_mult.values())
    if total_m < deg and 1 in [sp.Integer(1), sp.simplify(sp.Integer(1))]:
        # If 1 is actually a root, give it the remainder
        if any(sp.simplify(P.as_expr().subs({r: 1})) == 0 for _ in (0,)):
            rho_mult[sp.Integer(1)] = rho_mult.get(sp.Integer(1), 0) + (deg - total_m)
            total_m = sum(rho_mult.values())

    if total_m < deg and rho_mult:
        # give the rest to the first key (last resort)
        first = next(iter(rho_mult.keys()))
        rho_mult[first] += (deg - total_m)

    if _LOG.isEnabledFor(logging.DEBUG):
        _LOG.debug("roots_with_multiplicity: %s", rho_mult)

    return rho_mult


# ---- Characteristic basis (unshifted) ----
def _characteristic_basis(A: sp.Poly, k_sym: sp.Symbol) -> List[sp.Expr]:
    """
    Homogeneous solution basis for A:
      A(u) = a0 + a1 u + ... + an u^n (degree n)
      => x[k+n] + (a1/a0) x[k+n-1] + ... + (an/a0) x[k] = 0
      basis terms: k^j * rho^k for each root rho with multiplicity m -> j=0..m-1
    """
    n = A.degree()
    if n <= 0:
        return []

    # Normalize to a0 = 1
    a = [A.nth(i) for i in range(n + 1)]
    a0 = sp.simplify(a[0])
    a = [sp.simplify(ai / a0) for ai in a]

    r = sp.symbols('r_char')
    poly_char = r**n
    for j in range(1, n + 1):
        poly_char += a[j] * r**(n - j)
    poly_char = sp.simplify(sp.expand(poly_char))

    try:
        P = sp.Poly(poly_char, r)
    except Exception:
        P = sp.Poly(sp.expand(poly_char), r)

    roots_mult = _roots_with_multiplicity(P, r)
    if not roots_mult:
        return []

    basis: List[sp.Expr] = []
    k = k_sym
    for rho, mult in roots_mult.items():
        m = int(mult)
        for j in range(m):
            basis.append(sp.simplify((k**j) * (rho**k)))
    # Ensure length equals n (pad if needed)
    if len(basis) < n:
        # Prefer padding with further powers on rho=1 if present
        if sp.Integer(1) in roots_mult:
            have = roots_mult[sp.Integer(1)]
            for j in range(have, have + (n - len(basis))):
                basis.append(sp.simplify((k**j) * (sp.Integer(1)**k)))
        else:
            for _ in range(n - len(basis)):
                basis.append(sp.Integer(0)*k)  # harmless zero placeholder
    return basis[:n]


def _closed_form_via_rsolve_homog(A: sp.Poly, x_init: List[sp.Expr], k_sym: sp.Symbol) -> sp.Expr:
    """
    Robust homogeneous closed form for constant-coefficient recurrences.

    1) Try sympy.rsolve with ICs.
    2) If that fails, build characteristic basis symbolically.
    """
    n = A.degree()
    if n == 0:
        return sp.Integer(0)

    # Normalize so a0 = 1
    a = [A.nth(i) for i in range(n + 1)]
    a0 = sp.simplify(a[0])
    a = [sp.simplify(ai / a0) for ai in a]

    x = sp.Function('x')
    k = k_sym
    lhs = x(k + n)
    for j in range(1, n + 1):
        lhs += a[j] * x(k + n - j)
    eq = sp.Eq(sp.simplify(lhs), 0)
    ics = {x(i): sp.simplify(x_init[i]) for i in range(n)}

    # Prefer rsolve
    try:
        rs = sp.rsolve(eq, x(k), ics)
        if rs is not None:
            return sp.simplify(rs * sp.Heaviside(k_sym, 1))
    except Exception:
        pass

    # Build characteristic basis explicitly
    r = sp.symbols('r_char')
    poly_char = r**n
    for j in range(1, n + 1):
        poly_char += a[j] * r**(n - j)
    poly_char = sp.simplify(sp.expand(poly_char))

    try:
        P = sp.Poly(poly_char, r)
    except Exception:
        P = sp.Poly(sp.expand(poly_char), r)

    roots_mult = _roots_with_multiplicity(P, r)
    if not roots_mult:
        raise ValueError("Unable to obtain symbolic roots/multiplicities for the recurrence.")

    # Build basis metadata (j, rho)
    basis = []
    for rho, mult in roots_mult.items():
        m = int(mult)
        for j in range(m):
            basis.append((j, rho))
    if len(basis) < n:
        # pad with extra powers on rho=1 if available
        if sp.Integer(1) in roots_mult:
            have = roots_mult[sp.Integer(1)]
            for j in range(have, have + (n - len(basis))):
                basis.append((j, sp.Integer(1)))
        else:
            # fallback
            first_rho = list(roots_mult.keys())[0]
            while len(basis) < n:
                basis.append((0, first_rho))
    elif len(basis) > n:
        basis = basis[:n]

    # Solve for coefficients to match ICs x[0..n-1]
    A_mat = sp.zeros(n, n)
    b_vec = sp.Matrix([sp.simplify(x_init[i]) for i in range(n)])
    for row in range(n):
        kval = row
        for col, (jpow, rho) in enumerate(basis):
            A_mat[row, col] = sp.simplify((kval**jpow) * (rho**kval))

    try:
        C_sol = A_mat.LUsolve(b_vec)
    except Exception:
        C_sol = A_mat.pinv() * b_vec

    xk = sp.Integer(0)
    for coeff, (jpow, rho) in zip(C_sol, basis):
        xk += sp.simplify(coeff) * (k**jpow) * (rho**k)

    return sp.simplify(xk * sp.Heaviside(k_sym, 1))


def impulse_response_closed(A: sp.Poly, k_sym: sp.Symbol) -> sp.Expr:
    """
    Impulse response of H(u)=1/A(u):
    Solve sum_{i=0}^n a_i h[k-i] = δ[k] with a_0 != 0.
    We compute h[0..n-1] from the recurrence (unilateral), then solve the
    homogeneous equation with those ICs to get a clean closed form.
    """
    n = A.degree()
    if n == 0:
        a0 = sp.simplify(A.nth(0))
        return sp.simplify(sp.KroneckerDelta(k_sym, 0) / a0)

    # Coefficients a_i (no premature normalization)
    a = [A.nth(i) for i in range(n + 1)]
    a0 = sp.simplify(a[0])

    # Build the first n impulse samples correctly:
    # h[k] = ( δ[k] - sum_{i=1..n} a_i h[k-i] ) / a0
    h0 = [sp.Integer(0)] * n
    for kk in range(n):
        s = sp.KroneckerDelta(kk, 0)
        for j in range(1, min(n, kk) + 1):
            s -= a[j] * h0[kk - j]
        h0[kk] = sp.simplify(s / a0)

    # Closed form = homogeneous solve with those ICs
    h_closed = _closed_form_via_rsolve_homog(A, h0, k_sym)

    # Ensure unilateral support starts at k=0
    return sp.simplify(h_closed * sp.Heaviside(k_sym, 1))


# ---- Utilities to keep expressions tame ----
def _cleanup_heaviside_powers(expr: sp.Expr) -> sp.Expr:
    """Heaviside(x,1)**m  -> Heaviside(x,1)."""
    H = sp.Heaviside
    e = sp.simplify(expr)
    return sp.simplify(
        e.replace(
            lambda a: isinstance(a, sp.Pow) and a.base.func is H and len(a.base.args) >= 1
                      and a.exp.is_Integer and int(a.exp) > 1,
            lambda a: H(*((a.base.args[0], sp.Integer(1)) if len(a.base.args) == 1 else a.base.args))
        )
    )


# ---- Delay helper for B(u) ----
def _poly_min_exp_u(poly: sp.Poly) -> int:
    """Smallest exponent of u with nonzero coefficient in poly (>=0 if none)."""
    if poly.is_zero:
        return 0
    exps = [e for (e,), _ in poly.as_dict().items()]
    return int(min(exps)) if exps else 0


# ---- Homogeneous correction fitter (delay-aware row count & shift) ----
def _fit_closed_form_to_seq(
    A: sp.Poly,
    B: sp.Poly,
    xk_closed: sp.Expr,
    seq: List[sp.Expr],
    k_sym: sp.Symbol
) -> sp.Expr:
    """
    Add a homogeneous correction so the closed-form matches the unilateral
    recurrence samples.

    rows ≈ deg(A) + deg(B) + d + 2  (capped by len(seq)), where d = min exp of B.
    We build/evaluate the correction at k-d and **remove gated rows** from the system.
    Prefer exact linsolve on usable rows; fallback to LU / pinv.
    """
    n = A.degree()
    if n <= 0:
        return sp.simplify(_cleanup_heaviside_powers(xk_closed))

    # a0 = 1 normalization for characteristic polynomial
    a = [A.nth(i) for i in range(n + 1)]
    a0 = sp.simplify(a[0])
    a = [sp.simplify(ai / a0) for ai in a]

    r = sp.symbols('r_char')
    poly_char = r**n
    for j in range(1, n + 1):
        poly_char += a[j] * r**(n - j)
    poly_char = sp.simplify(sp.expand(poly_char))

    try:
        P = sp.Poly(poly_char, r)
    except Exception:
        P = sp.Poly(sp.expand(poly_char), r)

    # Symbolic roots with multiplicity
    roots_mult = _roots_with_multiplicity(P, r)
    if not roots_mult:
        return sp.simplify(_cleanup_heaviside_powers(xk_closed))

    # homogeneous basis terms k^j * rho^k
    basis_terms = []
    for rho, mult in roots_mult.items():
        m = int(mult)
        for j in range(m):
            basis_terms.append(sp.simplify((k_sym**j) * (rho**k_sym)))
    if not basis_terms:
        return sp.simplify(_cleanup_heaviside_powers(xk_closed))

    # Delay from B(u)
    d = max(_poly_min_exp_u(B), 0)

    # rows: include B’s degree span AND the gate loss 'd', +2 extra rows for stability
    rows = min(len(seq), n + max(B.degree(), 0) + d + 2)
    # guarantee enough usable rows: (rows - d) >= n
    if (rows - d) < n:
        rows = min(len(seq), d + n)

    if _LOG.isEnabledFor(logging.DEBUG):
        _LOG.debug("_fit_closed_form_to_seq:")
        _LOG.debug("  deg(A)=%d, deg(B)=%d, delay d=%d, rows=%d", A.degree(), B.degree(), d, rows)
        _LOG.debug("  basis_terms (len=%d)=%s", len(basis_terms), basis_terms)

    # Build system on k=0..rows-1; evaluate basis at (k-d) and DO NOT constrain gated rows
    M = sp.zeros(rows, len(basis_terms))
    b = sp.zeros(rows, 1)
    usable = []  # indices with kval >= 0
    for rix in range(rows):
        xr = sp.simplify(xk_closed.subs({k_sym: rix}))
        kval = rix - d
        if kval < 0:
            b[rix, 0] = sp.Integer(0)  # do not constrain
            continue

        usable.append(rix)
        br = sp.simplify(seq[rix] - xr)
        b[rix, 0] = br
        for cix, term in enumerate(basis_terms):
            M[rix, cix] = sp.simplify(term.subs({k_sym: kval}))

    # Reduce to usable sub-system (eliminate all-zero gated rows)
    if usable:
        Mu = sp.Matrix([M[i, :] for i in usable])
        bu = sp.Matrix([b[i, 0] for i in usable])
    else:
        Mu = sp.Matrix(M)
        bu = sp.Matrix([b[i, 0] for i in range(rows)])

    if _LOG.isEnabledFor(logging.DEBUG):
        _LOG.debug("  usable rows = %d (k=%d..%d)", len(usable), (usable[0] if usable else 0), (usable[-1] if usable else rows - 1))
        if _DUMP_MATS:
            _LOG.debug("  Mu=\n%s", Mu)
            _LOG.debug("  bu=\n%s", bu)

    # Solve for C: prefer exact linsolve, then LU, then pinv
    C = None
    solved_via = ""
    try:
        Cvars = sp.symbols(f"C0:{len(basis_terms)}")
        eqs = [sp.Eq(sum(Mu[i, j] * Cvars[j] for j in range(Mu.shape[1])), bu[i]) for i in range(Mu.shape[0])]
        sol = sp.linsolve(eqs, Cvars)
        if sol:
            sol_tuple = list(sol)[0]
            C = sp.Matrix([sp.simplify(si) for si in sol_tuple])
            solved_via = "linsolve"
    except Exception:
        C = None

    if C is None:
        try:
            C = Mu.LUsolve(bu)
            solved_via = "LUsolve"
        except Exception:
            C = Mu.pinv() * bu
            solved_via = "pinv"

    if _LOG.isEnabledFor(logging.DEBUG):
        _LOG.debug("  solved via %s; C=%s", solved_via, [sp.simplify(C[i, 0] if C.shape[1] == 1 else C[i]) for i in range(C.shape[0])])

    # Correction is gated and shifted by the same delay d
    corr = sp.Integer(0)
    H = sp.Heaviside(k_sym - d, 1)
    for idx, term in enumerate(basis_terms):
        coeff = C[idx, 0] if (isinstance(C, sp.MatrixBase) and C.shape[1] == 1) else C[idx]
        corr += sp.simplify(coeff) * term.subs({k_sym: k_sym - d}) * H

    xk_fixed = sp.simplify(_cleanup_heaviside_powers(xk_closed + corr))

    if _LOG.isEnabledFor(logging.DEBUG):
        diffs = []
        for rix in range(rows):
            lhs = sp.N(sp.simplify(xk_fixed.subs({k_sym: rix})))
            rhs = sp.N(sp.simplify(seq[rix]))
            diffs.append(_floatish(lhs - rhs))
        _LOG.debug("  post-correction diffs for k=0..%d: %s", rows - 1, diffs)

    return xk_fixed


def inverse_z_unilateral(XZ, z, k, N: Optional[int]):
    """
    Build Xu(u), get A(u), B(u), compute seq by convolution, and ALWAYS build
    a closed form via x[k] = sum_i b_i h[k-i] Heaviside(k-i, 1),
    then fit the closed form to the recurrence samples with a homogeneous
    correction (guarantees equality to the unilateral sequence).
    """
    u, Xu = Xu_from_Xz(XZ, z)
    A, B = rational_AB_in_u(Xu, u)
    n = A.degree()

    # Reference finite sequence (and unilateral ICs) from recurrence
    needN = max(n - 1, (N if N is not None else n - 1))
    seq = seq_by_convolution(A, B, needN)

    # Closed-form via symbolic convolution of h[k] with B
    if n == 0:
        # X(u) = B(u)/a0  =>  x[k] is just scaled impulses
        a0 = sp.simplify(A.nth(0))
        xk_closed = sp.Integer(0)
        for i in range(B.degree() + 1):
            bi = B.nth(i)
            if bi != 0:
                xk_closed += sp.simplify(bi/a0) * sp.KroneckerDelta(k, i)
        xk_closed = sp.simplify(xk_closed)
    else:
        h_closed = impulse_response_closed(A, k)
        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("impulse_response_closed: h[k]=%s", sp.simplify(h_closed))
        xk_closed = sp.Integer(0)
        for i in range(B.degree() + 1):
            bi = B.nth(i)
            if bi == 0:
                continue
            term = sp.simplify(bi) * h_closed.subs({k: k - i}) * sp.Heaviside(k - i, 1)
            xk_closed += sp.simplify(term)
        xk_closed = sp.simplify(xk_closed)

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("xk (pre-fit) = %s", sp.simplify(xk_closed))

        # Fit-to-seq homogeneous correction (delay-aware rows & shift)
        xk_closed = _fit_closed_form_to_seq(A, B, xk_closed, seq, k)

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("xk (post-fit)= %s", sp.simplify(xk_closed))

    # Extend seq if caller asked for more samples than needN
    if N is not None and N > needN:
        seq = seq_by_convolution(A, B, N)

    return sp.simplify(xk_closed), (seq if N is not None else None)


# ---------- Public "core" API ----------
def forward_z(expr, syms, subs: Dict = None):
    k, z, T, t = syms['k'], syms['z'], syms['T'], syms['t']
    subs = _normalize_subs(subs or {}, syms)
    xk = sp.sympify(expr, locals=syms)
    if subs:
        xk = xk.subs(subs)
    XZ_cf = forward_z_closed_form(xk, z, k)
    if XZ_cf is None:
        ZT = getattr(sp, "z_transform", None) or getattr(getattr(sp, "integrals", None), "transforms", None)
        if callable(ZT):
            try:
                XZ = ZT(xk, k, z, noconds=True)
            except TypeError:
                XZ = ZT.z_transform(xk, k, z, noconds=True)  # type: ignore
        else:
            XZ = sp.summation(sp.simplify(xk) * z**(-k), (k, 0, sp.oo))
    else:
        XZ = sp.simplify(XZ_cf)
    return xk, sp.simplify(XZ)


def forward_z_from_xt(xt, syms, subs: Dict = None):
    k, z, T, t = syms['k'], syms['z'], syms['T'], syms['t']
    subs = _normalize_subs(subs or {}, syms)
    xt_expr = sp.sympify(xt, locals=syms)
    xk = xt_expr.xreplace({t: k*T})
    if subs:
        xk = xk.subs(subs)
    return forward_z(xk, syms, subs={})  # already applied


def inverse_z(X, syms, N: Optional[int] = None, subs: Dict = None):
    k, z = syms['k'], syms['z']
    subs = _normalize_subs(subs or {}, syms)
    XZ = sp.apart(sp.simplify(sp.sympify(X, locals=syms)), z)

    # Early substitution stabilizes A,B when parameters are numeric
    XZ_sub = XZ
    if subs:
        try:
            XZ_sub = sp.apart(sp.simplify(XZ.subs(subs)), z)
        except Exception:
            XZ_sub = XZ

    try:
        xk_closed, seqN = inverse_z_unilateral(XZ_sub, z, k, N)
        if subs:
            xk_closed = sp.simplify(xk_closed.subs(subs))
            if seqN is not None:
                seqN = [sp.simplify(v.subs(subs)) for v in seqN]
    except Exception:
        IZT = getattr(sp, "inverse_z_transform", None) or getattr(getattr(sp, "integrals", None), "transforms", None)
        if callable(IZT):
            try:
                xk_closed = IZT(XZ_sub, z, k)
                seqN = None
            except Exception:
                xk_closed = None
                seqN = None
        else:
            xk_closed = None
            seqN = None
        if xk_closed is None:
            raise

    return xk_closed, seqN


def series_in_u(X, syms, N: int, subs: Dict = None):
    z = syms['z']
    subs = _normalize_subs(subs or {}, syms)
    XZ = sp.sympify(X, locals=syms)
    u = sp.Symbol('u')
    Xu = sp.simplify(XZ.subs({z: 1/u}))
    ser = sp.series(sp.together(Xu), u, 0, N + 1).removeO()
    poly = sp.Poly(sp.expand(ser), u)
    coeffs = [sp.Integer(0)] * (N + 1)
    for (pow_u,), val in poly.as_dict().items():
        if 0 <= pow_u <= N:
            coeffs[pow_u] = sp.simplify(val)
    if subs:
        coeffs = [sp.simplify(c.subs(subs)) for c in coeffs]
    return ser, coeffs


def scipy_residuez(num, den):
    return residuez(num, den)


def tf_util(num, den, N: int = 40, dt: float = 1.0, impulse=False, step=False, u_seq: Optional[List[float]] = None):
    if ct is None:
        raise RuntimeError("python-control not available. Install 'control'.")
    Gz = ct.TransferFunction(num, den, dt=float(dt))
    out = {"Gz": Gz}
    k = np.arange(0, int(N) + 1)
    if impulse:
        T, y = ct.impulse_response(Gz, T=k)
        out["impulse_T"] = T; out["impulse_y"] = y
    if step:
        T, y = ct.step_response(Gz, T=k)
        out["step_T"] = T; out["step_y"] = y
    if u_seq is not None:
        u = np.array(u_seq, dtype=float)
        if len(u) < len(k):
            u = np.r_[u, np.zeros(len(k) - len(u))]
        T, y = ct.forced_response(Gz, T=k, U=u)
        out["forced_T"] = T; out["forced_y"] = y
    return out


def solve_difference(a_coeffs: List[sp.Expr], rhs: Optional[sp.Expr], ics: Dict[Any, Any], syms, N: Optional[int] = None):
    k = syms['k']
    x = sp.Function('x')

    m = len(a_coeffs) - 1
    lhs = x(k + m)
    for j, aj in enumerate(a_coeffs[1:], 1):
        lhs += aj * x(k + m - j)
    eq = sp.Eq(lhs, rhs if rhs is not None else 0)

    try:
        sol = sp.simplify(sp.rsolve(eq, x(k), ics if ics else None))
    except Exception:
        if rhs is not None:
            raise RuntimeError("Fallback only implemented for homogeneous equations.")
        # build homogeneous fallback
        sol = _solve_diff_homog(a_coeffs, k, ics)

    seq = None
    if N is not None:
        seq = [sp.simplify(sol.subs({k: i})) for i in range(int(N) + 1)]
    return eq, sol, seq


def _solve_diff_homog(a_coeffs: List[sp.Expr], k_sym: sp.Symbol, ics: Dict[Any, Any]):
    m = len(a_coeffs) - 1
    if m <= 0:
        raise ValueError("Order must be >= 1.")
    r = sp.symbols('r')
    poly = r**m
    for j, aj in enumerate(a_coeffs[1:], 1):
        poly += aj * r**(m - j)
    poly = sp.expand(poly)
    roots_mult = sp.roots(poly)
    if not roots_mult:
        roots_list = sp.solve(sp.Eq(poly, 0), r)
        roots_mult = {rr: 1 for rr in roots_list}
    basis = []
    for rho, mult in roots_mult.items():
        for j in range(mult):
            basis.append((j, rho))
    if len(basis) != m:
        raise ValueError("Unable to construct basis.")
    xvals = []
    x = sp.Function('x')
    for i in range(m):
        found = None
        for kexpr, v in ics.items():
            if isinstance(kexpr, sp.AppliedUndef) and kexpr.func.__name__ == 'x':
                if kexpr.args[0].is_Integer and int(kexpr.args[0]) == i:
                    found = v
                    break
        if found is None:
            raise ValueError(f"Missing IC x{i}=...")
        xvals.append(sp.sympify(found))
    A = sp.zeros(m, m)
    for row in range(m):
        nval = row
        for col, (jpow, rho) in enumerate(basis):
            A[row, col] = sp.simplify((nval**jpow) * (rho**nval))
    try:
        solC = sp.Matrix(A).LUsolve(sp.Matrix(xvals))
    except Exception:
        solC = sp.Matrix(A).pinv() * sp.Matrix(xvals)
    n = k_sym
    xk = sp.Integer(0)
    for coeff, (jpow, rho) in zip(solC, basis):
        xk += sp.simplify(coeff) * (n**jpow) * (rho**n)
    return sp.simplify(xk)
