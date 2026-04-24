
from __future__ import annotations
from typing import Dict, Sequence, Tuple, List
import math
import numpy as np
from numpy.typing import NDArray
import sympy as sp
from .utils import expr_to_poly, to_real_if_close

def controllable_canonical(b: Sequence[float], a: Sequence[float]) -> Tuple[NDArray, NDArray, NDArray, NDArray]:
    a = list(a); b = list(b)
    n = len(a)
    if len(b) < n + 1:
        b += [0.0] * (n + 1 - len(b))

    A = np.zeros((n, n), dtype=float)
    for i in range(n - 1):
        A[i, i + 1] = 1.0
    A[-1, :] = -np.array(list(reversed(a)), dtype=float)

    B = np.zeros((n, 1), dtype=float); B[-1, 0] = 1.0

    b0 = b[0]
    C_row = [b[n - j + 1] - a[j - 1] * b0 for j in range(1, n + 1)]
    C = np.array([C_row], dtype=float)
    D = np.array([[b0]], dtype=float)
    return A, B, C, D

def observable_canonical(b: Sequence[float], a: Sequence[float]) -> Tuple[NDArray, NDArray, NDArray, NDArray]:
    Ac, Bc, Cc, Dc = controllable_canonical(b, a)
    return Ac.T.copy(), Cc.T.copy(), Bc.T.copy(), Dc.copy()

def jordan_or_diagonal(b: Sequence[float], a: Sequence[float]) -> Tuple[NDArray, NDArray, NDArray, NDArray, Dict[complex,int]]:
    z = sp.symbols('z')
    n = len(a)
    Dz = z**n + sum(sp.nsimplify(a[i]) * z**(n - 1 - i) for i in range(n))
    Nz = sum(sp.nsimplify(b[i]) * z**(n - i) for i in range(min(len(b), n + 1)))

    Dp = expr_to_poly(Dz, z)
    Np = expr_to_poly(Nz, z)
    if Np.degree() >= Dp.degree():
        _, R = sp.div(Np, Dp)
        Nz = R.as_expr()

    H = sp.together(sp.simplify(Nz / Dz))
    roots_mult: Dict[sp.Expr, int] = sp.roots(Dz)

    blocks = []
    for p_sym, m in roots_mult.items():
        if m == 1:
            val = sp.residue(H, z, p_sym)
            coeffs = [complex(sp.N(val))]
        else:
            coeffs = []
            expr = sp.together(sp.simplify((z - p_sym)**m * H))
            for k in range(1, m + 1):
                deriv = sp.diff(expr, z, m - k) if (m - k) > 0 else expr
                val = sp.limit(deriv, z, p_sym) / math.factorial(m - k)
                coeffs.append(complex(sp.N(val)))
        blocks.append((complex(sp.N(p_sym)), m, coeffs))

    total_n = sum(m for _, m, _ in blocks)
    A = np.zeros((total_n, total_n), dtype=complex)
    B = np.zeros((total_n, 1), dtype=complex)
    C = np.zeros((1, total_n), dtype=complex)

    idx = 0
    for p_val, m, coeffs in blocks:
        for i in range(m):
            A[idx + i, idx + i] = p_val
            if i < m - 1:
                A[idx + i, idx + i + 1] = 1.0
        B[idx + m - 1, 0] = 1.0
        C[0, idx:idx + m] = np.array(list(reversed(coeffs)), dtype=complex)
        idx += m

    D = np.array([[b[0] if len(b) > 0 else 0.0]], dtype=complex)
    multiplicities = {complex(sp.N(p)): int(m) for p, m in roots_mult.items()}
    return A, B, C, D, multiplicities

def realify_complex_pairs(A: NDArray, B: NDArray, C: NDArray, D: NDArray,
                           multiplicities: Dict[complex, int], quiet: bool = False) -> Tuple[NDArray, NDArray, NDArray, NDArray]:
    n = A.shape[0]
    tol = 1e-12
    used = set()
    A_blocks: List[NDArray] = []
    B_blocks: List[NDArray] = []
    C_blocks: List[NDArray] = []

    def is_real(x: complex) -> bool:
        return abs(complex(x).imag) < tol

    def add_real_chain(i0: int, m: int):
        A_blocks.append(A[i0:i0+m, i0:i0+m])
        B_blocks.append(B[i0:i0+m, :])
        C_blocks.append(C[:, i0:i0+m])
        for k in range(i0, i0 + m):
            used.add(k)

    i = 0
    while i < n:
        if i in used:
            i += 1; continue
        lam = A[i, i]
        if is_real(lam):
            m = 1
            while i + m < n and abs(A[i + m - 1, i + m]) > tol and is_real(A[i + m, i + m]) and abs(A[i + m, i + m] - lam) < tol:
                m += 1
            add_real_chain(i, m)
            i += m; continue

        j = None
        for k in range(i + 1, n):
            if k in used: continue
            if abs(A[k, k] - np.conj(lam)) < 1e-9 and abs(A[i, k]) < tol and abs(A[k, i]) < tol:
                j = k; break
        if j is None:
            if not quiet:
                print("[realblocks] complex pole without conjugate partner; leaving complex.")
            add_real_chain(i, 1)
            i += 1; continue

        Ac = np.array([[A[i, i], 0.0], [0.0, A[j, j]]], dtype=complex)
        Bc = np.array([[B[i, 0]], [B[j, 0]]], dtype=complex)
        Cc = np.array([[C[0, i], C[0, j]]], dtype=complex)

        S = np.array([[1.0+0j, 1.0+0j], [-1j, 1j]], dtype=complex)
        S_inv = np.linalg.inv(S)
        Ar = S @ Ac @ S_inv
        Br = S @ Bc
        Cr = Cc @ S_inv

        R = np.diag([0.5, 1.0])
        R_inv = np.linalg.inv(R)
        Ar = R @ Ar @ R_inv
        Br = R @ Br
        Cr = Cr @ R_inv

        A_blocks.append(to_real_if_close(Ar))
        B_blocks.append(to_real_if_close(Br))
        C_blocks.append(to_real_if_close(Cr))

        used.add(i); used.add(j)
        i += 1

    total = sum(blk.shape[0] for blk in A_blocks)
    A_out = np.zeros((total, total), dtype=float)
    B_out = np.zeros((total, 1), dtype=float)
    C_out = np.zeros((1, total), dtype=float)
    r = 0
    for Ab, Bb, Cb in zip(A_blocks, B_blocks, C_blocks):
        rr = Ab.shape[0]
        A_out[r:r+rr, r:r+rr] = to_real_if_close(Ab)
        B_out[r:r+rr, :] = to_real_if_close(Bb)
        C_out[:, r:r+rr] = to_real_if_close(Cb)
        r += rr
    return A_out, B_out, C_out, to_real_if_close(D)
