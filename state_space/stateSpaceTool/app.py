
from __future__ import annotations
from typing import Dict, List
from .apis import RunRequest, RunResult
from .io import parse_poly
from .core import controllable_canonical, observable_canonical, jordan_or_diagonal, realify_complex_pairs
from .design import pretty_tf_lines, latex_block, latex_tf, pretty_ss_lines, tf_brief_check, dump_realizations_json

class StateSpaceApp:
    """
    Orchestrates parsing, realizations, optional LaTeX and checks.
    """
    def run(self, req: RunRequest) -> RunResult:
        b, a = parse_poly(req.num, req.den, req.form, req.zeros, req.poles, req.gain)
        zm1, zdom = pretty_tf_lines(b, a)

        wanted = {s.strip().lower() for s in req.forms.split(",") if s.strip()}
        valid = {"cont", "obs", "diag", "jordan"}
        if not wanted.issubset(valid):
            raise ValueError(f"--forms must be subset of {valid}.")

        realizations: Dict[str, Dict[str, List[List[float]]]] = {}
        latex_chunks: List[str] = []

        if "cont" in wanted:
            Ac, Bc, Cc, Dc = controllable_canonical(b, a)
            realizations["cont"] = {"A": self._J(Ac), "B": self._J(Bc), "C": self._J(Cc), "D": self._J(Dc)}
            if req.latex or req.latex_out:
                latex_chunks.append(latex_block("Controllable canonical", Ac, Bc, Cc, Dc))

        if "obs" in wanted:
            Ao, Bo, Co, Do = observable_canonical(b, a)
            realizations["obs"] = {"A": self._J(Ao), "B": self._J(Bo), "C": self._J(Co), "D": self._J(Do)}
            if req.latex or req.latex_out:
                latex_chunks.append(latex_block("Observable canonical", Ao, Bo, Co, Do))

        AJ = BJ = CJ = DJ = mult = None
        if "diag" in wanted or "jordan" in wanted:
            AJ, BJ, CJ, DJ, mult = jordan_or_diagonal(b, a)
            all_simple = all(m == 1 for m in mult.values())
            transformed = False
            if req.realblocks and any(abs(k.imag) > 1e-12 and v == 1 for k, v in mult.items()):
                AJr, BJr, CJr, DJr = realify_complex_pairs(AJ, BJ, CJ, DJ, mult, quiet=req.quiet)
                transformed = True
            else:
                AJr, BJr, CJr, DJr = AJ, BJ, CJ, DJ

            if "diag" in wanted and (all_simple or transformed):
                realizations["diag"] = {"A": self._J(AJr), "B": self._J(BJr), "C": self._J(CJr), "D": self._J(DJr)}
                if req.latex or req.latex_out:
                    latex_chunks.append(latex_block("Diagonal canonical" + (" (real 2x2)" if transformed else ""), AJr, BJr, CJr, DJr))

            if "jordan" in wanted:
                realizations["jordan"] = {"A": self._J(AJr), "B": self._J(BJr), "C": self._J(CJr), "D": self._J(DJr)}
                if req.latex or req.latex_out:
                    latex_chunks.append(latex_block("Jordan canonical" + (" (real 2x2)" if transformed else ""), AJr, BJr, CJr, DJr))

        latex_out = None
        if req.latex or req.latex_out:
            Hz_zm1, Hz_z = latex_tf(b, a)
            tf_block = (
                r"\\paragraph*{Pulse transfer function}" "\\n"
                r"\\[ H(z) = " + Hz_zm1 + r" \\quad=\\quad " + Hz_z + r" \\]" "\\n"
            )
            latex_out = tf_block + "\\n".join(latex_chunks)
            if req.latex_out:
                with open(req.latex_out, "w", encoding="utf-8") as f:
                    f.write(latex_out)

        if req.json_out:
            dump_realizations_json(req.json_out, realizations)

        check_log = None
        if req.check != "off":
            if req.check == "brief":
                check_log = f"[check] {tf_brief_check(b, a, req.dt)}."
            else:
                try:
                    import sympy as sp, control as ct, numpy as np
                    Ac, Bc, Cc, Dc = controllable_canonical(b, a)
                    sys = ct.ss(Ac, Bc, Cc, Dc, req.dt)
                    num, den = ct.tfdata(ct.ss2tf(sys))
                    num = np.atleast_1d(np.array(num, dtype=float)).ravel()
                    den = np.atleast_1d(np.array(den, dtype=float)).ravel()
                    z = sp.symbols('z')
                    Nz = sum(sp.nsimplify(float(num[i])) * z**(len(num)-1-i) for i in range(len(num)))
                    Dz = sum(sp.nsimplify(float(den[i])) * z**(len(den)-1-i) for i in range(len(den)))
                    check_log = "[check] python-control ss->tf: " + sp.sstr(sp.simplify(Nz/Dz))
                except Exception as e:
                    check_log = f"[check] skip ({e})."

        return RunResult(realizations=realizations, latex=latex_out, check_log=check_log)

    @staticmethod
    def _J(M):
        import numpy as np
        from .utils import json_matrix
        return json_matrix(np.array(M))
