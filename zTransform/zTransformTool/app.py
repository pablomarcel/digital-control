#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py — Orchestrator for zTransformTool.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
import numpy as np
import sympy as sp

from .apis import RunRequest
from .utils import symbol_table
from .io import parse_subs, parse_coeffs_numeric, parse_coeffs_symbolic, export_sequence
from .design import box
from . import core

class ZTApp:
    def __init__(self, print_boxes: bool = True):
        self.syms = symbol_table()
        self.print_boxes = print_boxes

    def _maybe_print(self, s: str):
        if self.print_boxes and s:
            print(s, end="")

    # ---------- Modes ----------
    def run(self, req: RunRequest) -> Dict[str, Any]:
        subs = parse_subs(req.subs, self.syms)
        out: Dict[str, Any] = {"mode": req.mode}

        if req.mode == "forward":
            if not req.expr:
                raise ValueError("Provide expr for forward Z.")
            xk, XZ = core.forward_z(req.expr, self.syms, subs=subs)
            self._maybe_print(box("x[k]", xk, req.latex))
            self._maybe_print(box("X(z) = Z{x[k]}", XZ, req.latex))
            out["xk"] = xk; out["Xz"] = XZ
            return out

        if req.mode == "forward_xt":
            if not req.xt:
                raise ValueError("Provide xt for forward Z from x(t).")
            xk, XZ = core.forward_z_from_xt(req.xt, self.syms, subs=subs)
            self._maybe_print(box("x[k] = x_t(kT)", xk, req.latex))
            self._maybe_print(box("X(z) = Z{x[k]}", XZ, req.latex))
            out["xk"] = xk; out["Xz"] = XZ
            return out

        if req.mode == "inverse":
            if not req.X:
                raise ValueError("Provide X for inverse Z.")
            xk_closed, seqN = core.inverse_z(req.X, self.syms, N=req.N, subs=subs)
            self._maybe_print(box("x[k] = Z^{-1}{X(z)} (unilateral)", xk_closed, req.latex))
            out["xk_closed"] = xk_closed
            if req.N is not None:
                rows = list(range(int(req.N)+1))
                self._maybe_print("\n================\nSequence x[0..{}]\n================\n{}\n".format(req.N, [sp.simplify(v) for v in seqN]))
                export_sequence(rows, seqN, name="xk", export_csv=req.export_csv, export_json=req.export_json)
                out["seq"] = seqN
            return out

        if req.mode == "series":
            if not req.X or req.N is None:
                raise ValueError("Provide X and N for series.")
            ser, coeffs = core.series_in_u(req.X, self.syms, req.N, subs=subs)
            self._maybe_print(box("X(z) series in z^{-1}", ser, req.latex))
            rows = list(range(int(req.N)+1))
            export_sequence(rows, coeffs, name="coeff", export_csv=req.export_csv, export_json=req.export_json)
            out["series"] = ser; out["coeffs"] = coeffs
            return out

        if req.mode == "residuez":
            if not (req.num and req.den):
                raise ValueError("Provide --num and --den for residuez")
            b, a = parse_coeffs_numeric(req.num), parse_coeffs_numeric(req.den)
            r, p, kdir = core.scipy_residuez(b, a)
            print("\nResidues r_i:", r); print("Poles p_i:", p); print("Direct k:", kdir)
            out["r"] = r; out["p"] = p; out["kdir"] = kdir
            return out

        if req.mode == "tf":
            if not (req.num and req.den):
                raise ValueError("Provide --num and --den for tf")
            b, a = parse_coeffs_numeric(req.num), parse_coeffs_numeric(req.den)
            u_seq = None
            if req.u:
                u_seq = [float(x) for x in req.u.replace(',', ' ').split()]
            data = core.tf_util(b, a, N=int(req.N or 40), dt=float(req.dt), impulse=req.impulse, step=req.step, u_seq=u_seq)
            out.update(data)
            # Exports for impulse/step/forced if present
            if "impulse_y" in data:
                k = np.arange(0, int(req.N or 40)+1)
                export_sequence(k, data["impulse_y"], name="impulse", export_csv=req.export_csv, export_json=req.export_json)
            if "step_y" in data:
                k = np.arange(0, int(req.N or 40)+1)
                export_sequence(k, data["step_y"], name="step", export_csv=req.export_csv, export_json=req.export_json)
            if "forced_y" in data:
                k = np.arange(0, int(req.N or 40)+1)
                export_sequence(k, data["forced_y"], name="forced", export_csv=req.export_csv, export_json=req.export_json)
            return out

        if req.mode == "diff":
            # Either full recurrence in req.rec, or a-coeffs/rhs/ics
            if req.rec:
                eq = sp.sympify(req.rec, locals={**self.syms, "Eq": sp.Eq, "x": sp.Function('x')})
                a_coeffs = None; rhs = None
            else:
                if not req.a:
                    raise ValueError("Provide --a 'a0 a1 ... an'")
                a_coeffs = parse_coeffs_symbolic(req.a, self.syms)
                rhs = sp.sympify(req.rhs, locals=self.syms) if req.rhs else None
            ics = {}
            if req.ics:
                for piece in req.ics.replace(';', ',').split(','):
                    if not piece.strip(): continue
                    name, val = piece.split('=')
                    idx = int(name.strip().lower().replace('x', ''))
                    ics[sp.Function('x')(idx)] = sp.sympify(val, locals=self.syms)
            eq, sol, seq = core.solve_difference(a_coeffs if a_coeffs else a_coeffs or [1,], rhs, ics, self.syms, N=req.N)
            self._maybe_print(box("Difference equation", eq, req.latex))
            self._maybe_print(box("Closed-form x[k]", sol, req.latex))
            if seq is not None:
                rows = list(range(int(req.N)+1))
                export_sequence(rows, seq, name="xk", export_csv=req.export_csv, export_json=req.export_json)
            out["eq"] = eq; out["sol"] = sol; out["seq"] = seq
            return out

        raise ValueError(f"Unknown mode: {req.mode}")
