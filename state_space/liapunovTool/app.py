from __future__ import annotations
from dataclasses import asdict
from typing import Optional, Dict, Any
import sympy as sp

from .apis import RunRequest, RunResult
from .core import LyapunovSolver, PDClassifier
from .design import make_ct_latex, make_dt_latex
from .io import parse_matrix, save_text, out_path

DEFAULT_OUT_DIR = "state_space/liapunovTool/out"

class LyapunovApp:
    """High-level orchestrator: parse → solve → classify → (optional) save LaTeX."""
    def run(self, req: RunRequest) -> RunResult:
        if req.mode == "ct":
            if req.A is None or req.Q is None:
                raise ValueError("CT mode requires --A and --Q.")
            A = parse_matrix(req.A)
            Q = parse_matrix(req.Q)
            if req.evalf:
                A = sp.N(A, req.evalf)
                Q = sp.N(Q, req.evalf)
            P = LyapunovSolver.solve_ct(A, Q, req.hermitian)
            pd = PDClassifier.sylvester_pd(P, req.digits)
            latex_text = make_ct_latex(A, Q, P, req.hermitian) if req.latex or req.latex_out else None
            if req.latex_out and latex_text:
                save_text(req.latex_out if any(ch in req.latex_out for ch in "/\\")
                          else out_path(DEFAULT_OUT_DIR, req.latex_out), latex_text)
            return RunResult(mode="ct", hermitian=req.hermitian, P=P, pd_class=pd, latex_text=latex_text,
                             meta={"A": A, "Q": Q})

        if req.mode == "dt":
            if req.G is None or req.Q is None:
                raise ValueError("DT mode requires --G and --Q.")
            G = parse_matrix(req.G)
            Q = parse_matrix(req.Q)
            if req.evalf:
                G = sp.N(G, req.evalf)
                Q = sp.N(Q, req.evalf)
            P = LyapunovSolver.solve_dt(G, Q, req.hermitian)
            pd = PDClassifier.sylvester_pd(P, req.digits)
            latex_text = make_dt_latex(G, Q, P, req.hermitian) if req.latex or req.latex_out else None
            if req.latex_out and latex_text:
                save_text(req.latex_out if any(ch in req.latex_out for ch in "/\\")
                          else out_path(DEFAULT_OUT_DIR, req.latex_out), latex_text)
            return RunResult(mode="dt", hermitian=req.hermitian, P=P, pd_class=pd, latex_text=latex_text,
                             meta={"G": G, "Q": Q})

        if req.mode == "example":
            if req.which not in ("ogata_5_8", "ogata_5_9"):
                raise ValueError("Unknown example; choose ogata_5_8 or ogata_5_9.")
            if req.which == "ogata_5_8":
                A = parse_matrix("[[-1 -2]; [1 -4]]")
                Q = parse_matrix("[[1 0]; [0 1]]")
                if req.evalf:
                    A = sp.N(A, req.evalf); Q = sp.N(Q, req.evalf)
                P = LyapunovSolver.solve_ct(A, Q, False)
                pd = PDClassifier.sylvester_pd(P, req.digits)
                latex_text = make_ct_latex(A, Q, P, False) if req.latex or req.latex_out else None
                if req.latex_out and latex_text:
                    save_text(req.latex_out if any(ch in req.latex_out for ch in "/\\")
                              else out_path(DEFAULT_OUT_DIR, req.latex_out), latex_text)
                return RunResult(mode="ct", hermitian=False, P=P, pd_class=pd, latex_text=latex_text,
                                 meta={"example": "ogata_5_8", "A": A, "Q": Q})
            else:
                G = parse_matrix("[[0 1]; [-0.5 -1]]")
                Q = parse_matrix("[[1 0]; [0 1]]")
                if req.evalf:
                    G = sp.N(G, req.evalf); Q = sp.N(Q, req.evalf)
                P = LyapunovSolver.solve_dt(G, Q, False)
                pd = PDClassifier.sylvester_pd(P, req.digits)
                latex_text = make_dt_latex(G, Q, P, False) if req.latex or req.latex_out else None
                if req.latex_out and latex_text:
                    save_text(req.latex_out if any(ch in req.latex_out for ch in "/\\")
                              else out_path(DEFAULT_OUT_DIR, req.latex_out), latex_text)
                return RunResult(mode="dt", hermitian=False, P=P, pd_class=pd, latex_text=latex_text,
                                 meta={"example": "ogata_5_9", "G": G, "Q": Q})
        raise ValueError("Unsupported mode.")
