
from __future__ import annotations
from typing import Sequence, Tuple, Dict, List
import json
import numpy as np
from numpy.typing import NDArray
import sympy as sp
import control as ct
from .utils import sympy_matrix_from_numpy, to_real_if_close, zdomain_coeffs_from_ba, json_matrix

def s_one_line(expr: sp.Expr) -> str:
    return sp.sstr(sp.simplify(expr))

def pretty_tf_lines(b: Sequence[float], a: Sequence[float]) -> Tuple[str, str]:
    z = sp.symbols('z')
    n = len(a)
    num_zm1 = sum(sp.nsimplify(b[i]) * z**(-i) for i in range(min(len(b), n + 1)))
    den_zm1 = 1 + sum(sp.nsimplify(a[i]) * z**(-(i + 1)) for i in range(n))
    zm1 = s_one_line(sp.simplify(num_zm1 / den_zm1))

    Nz = sum(sp.nsimplify(b[i]) * z**(n - i) for i in range(min(len(b), n + 1)))
    Dz = z**n + sum(sp.nsimplify(a[i]) * z**(n - 1 - i) for i in range(n))
    zdom = s_one_line(sp.simplify(Nz / Dz))
    return zm1, zdom

def latex_matrix(M: NDArray) -> str:
    return sp.latex(sympy_matrix_from_numpy(M))

def latex_tf(b: Sequence[float], a: Sequence[float]) -> Tuple[str, str]:
    z = sp.symbols('z')
    n = len(a)
    num_zm1 = sum(sp.nsimplify(b[i]) * z**(-i) for i in range(min(len(b), n + 1)))
    den_zm1 = 1 + sum(sp.nsimplify(a[i]) * z**(-(i + 1)) for i in range(n))
    Nz = sum(sp.nsimplify(b[i]) * z**(n - i) for i in range(min(len(b), n + 1)))
    Dz = z**n + sum(sp.nsimplify(a[i]) * z**(n - 1 - i) for i in range(n))
    return sp.latex(sp.simplify(num_zm1/den_zm1)), sp.latex(sp.simplify(Nz/Dz))

def latex_block(title: str, A: NDArray, B: NDArray, C: NDArray, D: NDArray) -> str:
    Atex, Btex, Ctex, Dtex = map(latex_matrix, (A, B, C, D))
    return (
        rf"\\paragraph*{{{title}}}" "\\n"
        r"\\["
        r"\\begin{aligned}"
        r"x_{k+1} &= A\\,x_k + B\\,u_k,\\qquad &"
        r"y_k &= C\\,x_k + D\\,u_k,\\\\"
        rf"A &= {Atex},\\quad & B &= {Btex},\\\\"
        rf"C &= {Ctex},\\quad & D &= {Dtex}"
        r"\\end{aligned}"
        r"\\]"
        "\\n"
    )

def pretty_ss_lines(A: NDArray, B: NDArray, C: NDArray, D: NDArray) -> Tuple[str, str]:
    def mat_one_line(M: NDArray) -> str:
        M = np.atleast_2d(M)
        rows = []
        for row in M:
            def fmt(v: complex):
                re, im = float(np.real(v)), float(np.imag(v))
                if abs(im) < 1e-12:
                    return sp.sstr(sp.nsimplify(re))
                sign = " + " if im >= 0 else " - "
                return f"{sp.sstr(sp.nsimplify(re))}{sign}{sp.sstr(sp.nsimplify(abs(im)))}*I"
            rows.append("[" + ", ".join(fmt(x) for x in row) + "]")
        return "[" + "; ".join(rows) + "]"
    return (
        f"x(k+1) = {mat_one_line(A)} * x(k) + {mat_one_line(B)} * u(k)",
        f"y(k)   = {mat_one_line(C)} * x(k) + {mat_one_line(D)} * u(k)",
    )

def normalize_tf(num, den):
    num = np.array(num, dtype=float).ravel()
    den = np.array(den, dtype=float).ravel()
    s = den[0] if den.size else 1.0
    if s == 0:
        nz = np.flatnonzero(np.abs(den) > 1e-14)
        if nz.size == 0:
            return num, den
        s = den[nz[0]]
    return num / s, den / s

def tf_brief_check(b, a, dt: float) -> str:
    try:
        from .core import controllable_canonical
        Ac, Bc, Cc, Dc = controllable_canonical(b, a)
        sys = ct.ss(to_real_if_close(Ac), to_real_if_close(Bc), to_real_if_close(Cc), to_real_if_close(Dc), dt)
        num_c, den_c = ct.tfdata(ct.ss2tf(sys))
        import numpy as np
        num_c = np.atleast_1d(np.array(num_c, dtype=float)).ravel()
        den_c = np.atleast_1d(np.array(den_c, dtype=float)).ravel()
        num_c, den_c = normalize_tf(num_c, den_c)

        num_o, den_o = zdomain_coeffs_from_ba(b, a)
        num_o, den_o = normalize_tf(num_o, den_o)

        L = max(len(num_c), len(num_o))
        num_c = np.pad(num_c, (L-len(num_c), 0))
        num_o = np.pad(num_o, (L-len(num_o), 0))
        Ld = max(len(den_c), len(den_o))
        den_c = np.pad(den_c, (Ld-len(den_c), 0))
        den_o = np.pad(den_o, (Ld-len(den_o), 0))

        if (np.max(np.abs(num_c - num_o)) < 1e-9) and (np.max(np.abs(den_c - den_o)) < 1e-9):
            return "ok"
        return "mismatch"
    except Exception as e:
        return f"skip ({e})"

def dump_realizations_json(path: str, obj: Dict[str, Dict[str, List[List[float]]]]):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
