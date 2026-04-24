
from __future__ import annotations
from typing import List, Sequence, Tuple
import numpy as np
from numpy.typing import NDArray
import sympy as sp

def to_float_list(txt: str | None) -> List[float]:
    if not txt:
        return []
    parts = [p for p in txt.replace(",", " ").replace(";", " ").split() if p]
    return [float(p) for p in parts]

def coeffs_desc_to_expr(coeffs: Sequence[float], z: sp.Symbol) -> sp.Expr:
    n = len(coeffs) - 1
    expr = sp.Integer(0)
    for i, c in enumerate(coeffs):
        expr += sp.nsimplify(c) * z**(n - i)
    return sp.simplify(expr)

def expr_to_poly(expr: sp.Expr, z: sp.Symbol) -> sp.Poly:
    return sp.Poly(sp.simplify(expr), z, domain=sp.EX)

def to_real_if_close(M: NDArray, tol: float = 1e-12) -> NDArray:
    if np.iscomplexobj(M) and np.max(np.abs(M.imag)) < tol:
        return M.real.astype(float)
    return M

def json_matrix(M: NDArray, tol: float = 1e-12):
    out = []
    for row in np.atleast_2d(M):
        r = []
        for v in row:
            v = complex(v)
            r.append(float(v.real) if abs(v.imag) < tol else [float(v.real), float(v.imag)])
        out.append(r)
    return out

def sympy_matrix_from_numpy(M: NDArray) -> sp.Matrix:
    m, n = np.atleast_2d(M).shape
    data = []
    for i in range(m):
        row = []
        for j in range(n):
            z = complex(M[i, j])
            if abs(z.imag) < 1e-14:
                row.append(sp.nsimplify(z.real))
            else:
                row.append(sp.nsimplify(z.real) + sp.nsimplify(z.imag) * sp.I)
        data.append(row)
    return sp.Matrix(data)

def zdomain_coeffs_from_ba(b: Sequence[float], a: Sequence[float]) -> Tuple[List[float], List[float]]:
    n = len(a)
    den_desc = [1.0] + [float(ai) for ai in a]
    b = list(b[:n+1]) + [0.0] * max(0, n + 1 - len(b))
    num_desc = [float(b[i]) for i in range(n+1)]
    return num_desc, den_desc
