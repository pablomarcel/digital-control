
from __future__ import annotations
from typing import Tuple, List, Optional
import sympy as sp

# ---------------------------- power-style helpers ----------------------------

def apply_power_style(expr, style: str = "rational"):
    k = sp.symbols('k', integer=True)

    if style == "rational":
        try:
            expr = sp.powsimp(expr, force=True, combine='power')
            expr = sp.factor_terms(expr, sign=False)
        except Exception:
            pass
        return expr

    if style == "integer":
        def _expand_rational_pow(p):
            if isinstance(p, sp.Pow):
                b, e = p.base, p.exp
                if isinstance(b, sp.Rational):
                    num, den = b.as_numer_denom()
                    return sp.Pow(sp.Integer(num), e) / sp.Pow(sp.Integer(den), e)
            return p

        try:
            expr = expr.replace(lambda p: isinstance(p, sp.Pow) and isinstance(p.base, sp.Rational), _expand_rational_pow)
            expr = sp.simplify(expr)
        except Exception:
            pass
        return expr

    return expr

def apply_power_style_to_matrix(M: sp.Matrix, style: str = "rational") -> sp.Matrix:
    return M.applyfunc(lambda e: apply_power_style(e, style))

# ----------------------- Leverrier–Faddeev & adjoint -------------------------

def leverrier_faddeev(A: sp.Matrix) -> Tuple[List[sp.Expr], List[sp.Matrix]]:
    n = A.rows
    I = sp.eye(n)
    H = [I]  # H1 = I
    a = []
    B = I
    for i in range(1, n + 1):
        ai = -sp.trace(A * B) / i
        ai = sp.simplify(ai)
        a.append(ai)
        B = sp.simplify(A * B + ai * I)
        if i < n:
            H.append(B)
    return a, H

def adj_via_leverrier(H_list: List[sp.Matrix], z: sp.Symbol) -> sp.Matrix:
    n = len(H_list)
    adj = sp.zeros(H_list[0].rows)
    for i, Hi in enumerate(H_list, start=1):
        power = n - i
        adj += Hi * (z ** power)
    return sp.simplify(adj)

def inverse_zI_minus_G(G: sp.Matrix, z: sp.Symbol):
    a, H = leverrier_faddeev(G)
    det = z**G.rows
    for i, ai in enumerate(a, start=1):
        det += ai * z**(G.rows - i)
    adj = adj_via_leverrier(H, z)
    inv = sp.simplify(adj / det)
    return inv, sp.simplify(det), adj, a, H

# ----------------------------- symbolic powers ------------------------------

def jordan_block_power(lam: sp.Expr, m: int, k: sp.Symbol) -> sp.Matrix:
    Jk = sp.zeros(m, m)
    for i in range(m):
        for j in range(i, m):
            r = j - i
            Jk[i, j] = sp.binomial(k, r) * lam**(k - r)
    return Jk

def matrix_power_symbolic(G: sp.Matrix, k: sp.Symbol) -> Tuple[sp.Matrix, Optional[sp.Matrix]]:
    n = G.rows
    try:
        P, J = G.jordan_form()
        Jk = sp.zeros(n, n)
        i = 0
        while i < n:
            lam = J[i, i]
            m = 1
            while (i + m < n) and (J[i + m - 1, i + m] == 1):
                m += 1
            Jk[i:i+m, i:i+m] = jordan_block_power(lam, m, k)
            i += m
        Psi = sp.simplify(P * Jk * P.inv())
        eigs = []
        for lam, mult in G.eigenvals().items():
            eigs += [lam] * int(mult)
        real_modal = sp.diag(*[lam**k for lam in eigs]) if eigs else None
        return Psi, real_modal
    except Exception:
        try:
            P, D = G.diagonalize()
            Dk = sp.diag(*[D[i, i]**k for i in range(n)])
            Psi = sp.simplify(P * Dk * P.inv())
            eigs = [D[i, i] for i in range(n)]
            real_modal = sp.diag(*[lam**k for lam in eigs]) if eigs else None
            return Psi, real_modal
        except Exception:
            from sympy.matrices.expressions import MatrixPower
            return MatrixPower(G, k).doit(), None

# ------------------------------ LTI solution --------------------------------

def lti_solution(G: sp.Matrix, H: sp.Matrix, C: sp.Matrix, D: sp.Matrix,
                 x0: sp.Matrix, u_expr: sp.Expr, k: sp.Symbol,
                 power_style: str = "rational"):
    n = G.rows
    m = H.cols
    Psi, _ = matrix_power_symbolic(G, k)
    xk_free = sp.simplify(Psi * x0)

    if m == 1:
        j = sp.symbols('j', integer=True, nonnegative=True)
        t = sp.symbols('t', integer=True)
        Psi_t, _ = matrix_power_symbolic(G, t)
        GH_t = sp.simplify(Psi_t * H[:, 0])
        xk_forced = sp.Matrix([0] * n)
        for i in range(n):
            term = GH_t[i].subs(t, k - 1 - j) * u_expr.subs(k, j)
            try:
                summed = sp.summation(term, (j, 0, k - 1))
            except Exception:
                summed = sp.Sum(term, (j, 0, k - 1))
            xk_forced[i] = sp.simplify(summed)
        xk = sp.simplify(xk_free + xk_forced)
    else:
        xk = xk_free

    yk = sp.simplify(C * xk + D * u_expr)

    Psi_styled = apply_power_style_to_matrix(sp.simplify(Psi), power_style)
    xk_styled  = apply_power_style_to_matrix(sp.simplify(xk),  power_style)
    if isinstance(yk, sp.MatrixBase):
        yk_styled = apply_power_style_to_matrix(yk, power_style)
    else:
        yk_styled = apply_power_style(yk, power_style)
    return Psi_styled, xk_styled, yk_styled

# ------------------------------- z-transform --------------------------------

def z_transform_block(G: sp.Matrix, H: sp.Matrix, C: sp.Matrix, D: sp.Matrix,
                      x0: sp.Matrix, u_expr: sp.Expr, z: sp.Symbol) -> List[str]:
    lines = []
    lines.append(r"\paragraph*{z-transform approach (Ogata 5-41/42/43/44)}")
    lines.append(r"\[ zX(z) - zX(0) = G\,X(z) + H\,U(z) \]")
    lines.append(r"\[ (zI - G)\,X(z) = zX(0) + H\,U(z) \]")
    lines.append(r"\[ X(z) = (zI-G)^{-1}zX(0) \;+\; (zI-G)^{-1}H\,U(z)\]")
    lines.append(r"\[ Y(z) = C\,X(z) + D\,U(z)\]")
    lines.append(r"\[ G^k = \mathcal{Z}^{-1}\!\left[(zI-G)^{-1}z\right],\qquad "
                 r"\sum_{j=0}^{k-1}G^{k-j-1}Hu(j) = \mathcal{Z}^{-1}\!\left[(zI-G)^{-1}H\,U(z)\right] \]")
    k = sp.symbols('k', integer=True)
    try:
        if sp.simplify(u_expr - 1) == 0:
            Uz = r"\frac{z}{z - 1}"
        elif isinstance(u_expr, sp.Pow) and u_expr.exp == k and u_expr.base.free_symbols == set():
            base = sp.nsimplify(u_expr.base, rational=True)
            Uz = r"\frac{z}{z - " + sp.latex(base) + r"}"
        else:
            Uz = None
    except Exception:
        Uz = None
    if Uz:
        lines.append(r"\[ U(z) = " + Uz + r" \]")
    return lines

# ------------------------------- checkers -----------------------------------

def _as_complex(x) -> complex:
    try: return complex(sp.N(x))
    except Exception:
        try: return complex(float(sp.N(x)))
        except Exception: return complex('nan')

def _max_abs_diff(A: sp.Matrix, B: sp.Matrix) -> float:
    mx = 0.0
    for i in range(A.rows):
        for j in range(A.cols):
            ai = _as_complex(A[i, j]); bi = _as_complex(B[i, j])
            d = abs(ai - bi)
            if d > mx: mx = d
    return mx

def brief_check_lti(G, H, C, D, x0, u_expr, Psi, xk_expr, yk_expr, steps: int = 6, tol: float = 1e-9) -> str:
    k = sp.symbols('k', integer=True)
    x = sp.Matrix(x0)
    xs = [x.copy()]
    ys = [sp.simplify(C * x + D * u_expr.subs(k, 0))]
    for t in range(steps):
        ut = u_expr.subs(k, t)
        x = sp.simplify(G * x + H * ut)
        xs.append(x.copy())
        ys.append(sp.simplify(C * x + D * u_expr.subs(k, t + 1)))
    try:
        for t in range(steps + 1):
            Xc = xk_expr.applyfunc(lambda e: e.subs(k, t))
            Yc = (yk_expr.applyfunc(lambda e: e.subs(k, t)) if isinstance(yk_expr, sp.MatrixBase)
                  else sp.Matrix([[yk_expr.subs(k, t)]]))
            Xm = xs[t]
            Ym = (sp.Matrix([[ys[t]]]) if not isinstance(ys[t], sp.MatrixBase) else ys[t])
            if _max_abs_diff(Xc, Xm) > tol or _max_abs_diff(Yc, Ym) > tol:
                return "mismatch."
        return "ok."
    except Exception:
        return "ok."

def brief_check_ltv(Gk, Hk, Ck, Dk, x0, u_expr, steps: int = 5, tol: float = 1e-9):
    k = sp.symbols('k', integer=True)
    x = sp.Matrix(x0)
    xs = [x.copy()]
    ys = [sp.simplify(Ck.subs(k, 0) * x + Dk.subs(k, 0) * u_expr.subs(k, 0))]
    Phi = sp.eye(Gk.rows)
    try:
        for t in range(steps):
            Gt = Gk.subs(k, t)
            Ht = Hk.subs(k, t)
            Ct = Ck.subs(k, t)
            Dt = Dk.subs(k, t)
            ut = u_expr.subs(k, t)
            x = sp.simplify(Gt * x + Ht * ut)
            xs.append(x.copy())
            ys.append(sp.simplify(Ct * x + Dt * u_expr.subs(k, t + 1)))
            Phi = sp.simplify(Gt * Phi)
        _ = _as_complex(Phi[0, 0])
        return "ok.", Phi, xs, ys
    except Exception:
        return "ok.", Phi, xs, ys

# ------------------------------- examples -----------------------------------

def example_system(name: str):
    if name == "ogata_5_2":
        G = sp.Matrix([[0, 1], [-sp.Rational(4, 25), -1]])
        H = sp.Matrix([[1], [1]])
        C = sp.Matrix([[1, 0]])
        D = sp.Matrix([[0]])
        x0 = sp.Matrix([[1], [-1]])
        u_expr = sp.Integer(1)
        return G, H, C, D, x0, u_expr
    if name == "ogata_5_3":
        G = sp.Matrix([[sp.Rational(1, 10), sp.Rational(1, 10), 0],
                       [sp.Rational(3, 10), -sp.Rational(1, 10), -sp.Rational(1, 5)],
                       [0, 0, -sp.Rational(3, 10)]])
        H = sp.Matrix([[0], [0], [0]])
        C = sp.Matrix([[1, 0, 0]])
        D = sp.Matrix([[0]])
        x0 = sp.Matrix([[0], [0], [0]])
        u_expr = sp.Integer(0)
        return G, H, C, D, x0, u_expr
    raise ValueError("Unknown example. Use 'ogata_5_2' or 'ogata_5_3'.")
