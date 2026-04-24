from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from math import atan2

import sympy as sp

from .utils import sstr, fmt_row, fmt_vec, banner
from .core import (
    Tolerances, jury_table_vectors, jury_inequalities,
    schur_reflection_coeffs, schur_inequalities,
    bilinear_Q_from_coeffs, poly_coeffs_desc, routh_array,
    routh_first_column_inequalities, print_conditions,
    compute_roots, any_radius_on_unit_circle, verdict_from
)

@dataclass
class MethodText:
    ascii: str
    verdict: str

@dataclass
class EvalSummary:
    K: float
    roots: List[List[float]]
    radii: List[float]
    omega_d: Optional[float] = None

class StabilityDesigner:
    def __init__(self, tols: Tolerances):
        self.tols = tols

    def _jury_text(self, P, a_fwd, z, subs_eval):
        rows = jury_table_vectors(a_fwd)
        txt = banner("=== JURY TABLE (ASCII) ===")
        rno = 1
        for tag, top, bot in rows:
            txt += fmt_row(f"Row {rno:>2} [{tag}]:", top) + "\n"; rno += 1
            txt += fmt_row(f"Row {rno:>2}:", bot) + "\n"; rno += 1
            txt += "-"*78 + "\n"
        ineqs, labels = jury_inequalities(P, a_fwd, z)
        t2, all_true, any_equal = print_conditions(ineqs, labels, subs_eval, self.tols)
        txt += t2
        verdict = verdict_from(all_true, any_equal) or "See inequalities / solve_range"
        return txt, verdict, ineqs, labels

    def _schur_text(self, P, a_fwd, z, subs_eval):
        kappas, polys = schur_reflection_coeffs(a_fwd)
        txt = banner("=== SCHUR–COHN (reflection coefficients) ===")
        for i in range(len(kappas)):
            txt += f"Stage {i}: poly a^{i} = [{fmt_vec(polys[i])}]\n"
            txt += f"  κ_{i} = {sstr(kappas[i])}\n"
        txt += f"Stage {len(kappas)}: poly a^{len(kappas)} = [{fmt_vec(polys[-1])}]\n"
        ineqs, labels, _ = schur_inequalities(P, a_fwd, z)
        t2, all_true, any_equal = print_conditions(ineqs, labels, subs_eval, self.tols)
        txt += t2
        verdict = verdict_from(all_true, any_equal) or "See inequalities / solve_range"
        return txt, verdict, ineqs, labels

    def _routh_text(self, a_fwd, subs_eval):
        w = sp.symbols('w', complex=True)
        Q = bilinear_Q_from_coeffs(a_fwd, w)
        coeffs_desc = poly_coeffs_desc(Q, w)
        arr = routh_array(coeffs_desc)
        txt = banner("=== ROUTH ARRAY (Bilinear map, LHP test) ===")
        txt = "\n--- Bilinear transform (polynomial construction) ---\n" + \
              f"Q(w) = {sp.sstr(Q)}\n" + \
              "b0..bn (desc) = [" + ", ".join(sstr(c) for c in coeffs_desc) + "]\n" + \
              txt
        for i, row in enumerate(arr):
            txt += fmt_row(f"Row {i:>2}:", row) + "\n"
        ineqs, labels = routh_first_column_inequalities(arr)
        t2, all_true, any_equal = print_conditions(ineqs, labels, subs_eval, self.tols)
        txt += t2
        verdict = verdict_from(all_true, any_equal) or "See inequalities / solve_range"
        return txt, verdict, ineqs, labels, Q, coeffs_desc, arr

    def run_methods(self, method: str, P, a_fwd, z, K, subs_eval, solve_range: bool, T: Optional[float]):
        out: Dict[str, Dict[str, Any]] = {}
        boundary_via_roots = False
        radii_eval = None
        roots_eval = None

        if subs_eval is not None:
            try:
                roots_eval = compute_roots(a_fwd, subs_eval)
                radii_eval = [float(abs(r)) for r in roots_eval]
                boundary_via_roots = any_radius_on_unit_circle(radii_eval, self.tols)
            except Exception:
                pass

        if method in ("jury","all"):
            txt, verdict, ineqsJ, labelsJ = self._jury_text(P, a_fwd, z, subs_eval)
            solJ = sp.reduce_inequalities(ineqsJ, K) if (solve_range and K is not None) else None
            if verdict != "UNSTABLE" and boundary_via_roots:
                verdict = "CRITICAL (boundary via roots)"
            out["jury"] = {
                "text": txt,
                "verdict": verdict,
                "inequalities": [{"label": lab, "expr": sp.sstr(e)} for lab,e in zip(labelsJ, ineqsJ)],
                "solution_param": (sp.sstr(solJ) if solJ is not None else None),
            }

        if method in ("schur","all"):
            txt, verdict, ineqsS, labelsS = self._schur_text(P, a_fwd, z, subs_eval)
            solS = sp.reduce_inequalities(ineqsS, K) if (solve_range and K is not None) else None
            if verdict != "UNSTABLE" and boundary_via_roots:
                verdict = "CRITICAL (boundary via roots)"
            out["schur"] = {
                "text": txt,
                "verdict": verdict,
                "inequalities": [{"label": lab, "expr": sp.sstr(e)} for lab,e in zip(labelsS, ineqsS)],
                "solution_param": (sp.sstr(solS) if solS is not None else None),
            }

        if method in ("bilinear","all"):
            txt, verdict, ineqsR, labelsR, Q, coeffs_desc, arr = self._routh_text(a_fwd, subs_eval)
            solR = sp.reduce_inequalities(ineqsR, K) if (solve_range and K is not None) else None
            if verdict != "UNSTABLE" and boundary_via_roots:
                verdict = "CRITICAL (boundary via roots)"
            out["bilinear"] = {
                "text": txt,
                "verdict": verdict,
                "Q_w": sp.sstr(Q),
                "coeffs_desc": [sp.sstr(c) for c in coeffs_desc],
                "routh_array": [[sp.sstr(x) for x in row] for row in arr],
                "inequalities": [{"label": lab, "expr": sp.sstr(e)} for lab,e in zip(labelsR, ineqsR)],
                "solution_param": (sp.sstr(solR) if solR is not None else None),
            }

        eval_summary = None
        if subs_eval is not None and roots_eval is not None:
            kval = float(subs_eval[list(subs_eval.keys())[0]])
            Omega = None
            if (T is not None) and (len(roots_eval) == 2) and boundary_via_roots:
                # Angle of the (complex) root using atan2(imag, real)
                ang = abs(atan2(roots_eval[0].imag, roots_eval[0].real))
                Omega = ang / float(T)
            eval_summary = {
                "K": kval,
                "roots": [[float(r.real), float(r.imag)] for r in roots_eval],
                "radii": [float(r) for r in radii_eval] if radii_eval is not None else None,
                "omega_d": Omega
            }

        return out, eval_summary
