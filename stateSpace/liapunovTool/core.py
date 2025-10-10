from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
import sympy as sp

@dataclass
class PUnknown:
    P: sp.Matrix
    unknowns: List[sp.Symbol]

class PBuilder:
    @staticmethod
    def build(n: int, hermitian: bool) -> PUnknown:
        P = sp.zeros(n, n)
        unknowns: List[sp.Symbol] = []
        for i in range(n):
            pii = sp.symbols(f"p{i+1}{i+1}", real=True)
            P[i, i] = pii
            unknowns.append(pii)
        for i in range(n):
            for j in range(i+1, n):
                if not hermitian:
                    pij = sp.symbols(f"p{i+1}{j+1}", real=True)
                    P[i, j] = pij
                    P[j, i] = pij
                    unknowns.append(pij)
                else:
                    a = sp.symbols(f"a{i+1}{j+1}", real=True)
                    b = sp.symbols(f"b{i+1}{j+1}", real=True)
                    pij = a + sp.I*b
                    P[i, j] = pij
                    P[j, i] = sp.conjugate(pij)
                    unknowns.extend([a, b])
        return PUnknown(P, unknowns)

class LyapunovSolver:
    @staticmethod
    def solve_ct(A: sp.Matrix, Q: sp.Matrix, hermitian: bool) -> sp.Matrix:
        n = A.shape[0]
        pu = PBuilder.build(n, hermitian)
        Aop = A.conjugate().T if hermitian else A.T
        M = sp.expand(Aop*pu.P + pu.P*A + Q)
        eqs = []
        for i in range(n):
            for j in range(n):
                e = sp.simplify(M[i, j])
                if hermitian:
                    eqs.append(sp.Eq(sp.re(e), 0))
                    eqs.append(sp.Eq(sp.im(e), 0))
                else:
                    eqs.append(sp.Eq(e, 0))
        sol = sp.solve(eqs, pu.unknowns, dict=True, simplify=True)
        if not sol:
            raise ValueError("Lyapunov CT solver: no solution found (check A, Q).")
        Psol = sp.simplify(pu.P.subs(sol[0]))
        Psol = sp.simplify(sp.expand_complex(Psol)).xreplace({sp.conjugate(sp.I): -sp.I})
        return Psol

    @staticmethod
    def solve_dt(G: sp.Matrix, Q: sp.Matrix, hermitian: bool) -> sp.Matrix:
        n = G.shape[0]
        pu = PBuilder.build(n, hermitian)
        Gop = G.conjugate().T if hermitian else G.T
        M = sp.expand(Gop*pu.P*G - pu.P + Q)
        eqs = []
        for i in range(n):
            for j in range(n):
                e = sp.simplify(M[i, j])
                if hermitian:
                    eqs.append(sp.Eq(sp.re(e), 0))
                    eqs.append(sp.Eq(sp.im(e), 0))
                else:
                    eqs.append(sp.Eq(e, 0))
        sol = sp.solve(eqs, pu.unknowns, dict=True, simplify=True)
        if not sol:
            raise ValueError("Lyapunov DT solver: no solution found (check G, Q).")
        Psol = sp.simplify(pu.P.subs(sol[0]))
        Psol = sp.simplify(sp.expand_complex(Psol)).xreplace({sp.conjugate(sp.I): -sp.I})
        return Psol

class PDClassifier:
    @staticmethod
    def sylvester_pd(P: sp.Matrix, digits: int = 16) -> str:
        n = P.shape[0]
        minors = [sp.simplify(sp.det(P[:k, :k])) for k in range(1, n+1)]
        exact_flags = []
        for m in minors:
            try:
                if m.is_positive:
                    exact_flags.append(True)
                elif m.is_negative or m.is_zero:
                    return "not positive definite"
                else:
                    exact_flags.append(None)
            except Exception:
                exact_flags.append(None)
        if all(f is True for f in exact_flags):
            return "positive definite"
        try:
            minors_num = [sp.N(m, digits) for m in minors]
            if all(sp.re(mn) > 0 for mn in minors_num):
                return "positive definite"
            if any(sp.re(mn) <= 0 for mn in minors_num):
                return "not positive definite"
        except Exception:
            pass
        return "unknown"
