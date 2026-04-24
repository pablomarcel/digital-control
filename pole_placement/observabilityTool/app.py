from __future__ import annotations
import logging
import os
import json
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from numpy.linalg import eig
try:
    import sympy as sp
except Exception:
    sp = None

from .apis import RunRequest, RunResult
from .utils import pkg_outdir
from .io import parse_matrix_string, load_from_json, save_json
from .core import (
    observability_matrix, rank_numeric, pbh_observable,
    gramian_observability_ct, gramian_observability_dt,
    finite_gramian_ct, finite_gramian_dt,
    minreal_observable, stable_ct, stable_dt
)
from .design import capture_pretty_text

logger = logging.getLogger(__name__)

class ObservabilityApp:
    def run(self, req: RunRequest) -> RunResult:
        logger.info(
            "Starting ObservabilityApp.run",
            extra={
                "discrete": req.discrete,
                "horizon": req.horizon,
                "tol": req.tol,
                "do_pbh": req.do_pbh,
                "do_gram": req.do_gram,
                "finite_dt": req.finite_dt,
                "finite_ct": req.finite_ct,
                "do_minreal": req.do_minreal,
                "pretty": req.pretty,
                "run_name": req.name,
            },
        )

        # Load system
        if req.json_in:
            A, C, disc = load_from_json(req.json_in)
            discrete = bool(req.discrete or disc)
            logger.debug("Loaded from JSON", extra={"json_in": req.json_in})
        else:
            if not req.A or not req.C:
                raise ValueError("When not using --json, both --A and --C are required.")
            A = parse_matrix_string(req.A)
            logger.debug("Parsed A from string", extra={"A": str(A)})
            C = parse_matrix_string(req.C)
            logger.debug("Parsed C from string", extra={"C": str(C)})
            discrete = bool(req.discrete)

        n = A.shape[0]
        if A.shape[0] != A.shape[1]:
            raise ValueError("A must be square.")
        if C.shape[1] != n:
            raise ValueError(f"C must have {n} columns.")
        logger.debug("Shapes", extra={"n": int(n), "m": int(C.shape[0])})

        # Observability matrix and rank
        Obsv = observability_matrix(A, C, req.horizon)
        logger.debug("Built observability matrix", extra={"rows": int(Obsv.shape[0]), "cols": int(Obsv.shape[1])})
        r_num = rank_numeric(Obsv, tol=req.tol)
        full_obsv = (r_num == n)
        logger.info("rank(Obsv)", extra={"rank": int(r_num), "n": int(n)})
        eigvals, _ = eig(A)
        logger.debug("Eigenvalues computed", extra={"eigvals": [complex(z) for z in eigvals]})

        # SymPy exact rank
        sym_rank = None
        if req.symbolic and sp is not None:
            A_sym = sp.Matrix(A.tolist())
            C_sym = sp.Matrix(C.tolist())
            h = n if req.horizon is None else req.horizon
            O_sym = sp.Matrix.vstack(*[C_sym * (A_sym**k) for k in range(h)])
            sym_rank = int(O_sym.rank())

        # PBH
        pbh_pass = None
        pbh_details = None
        if req.do_pbh:
            pbh_pass, pbh_details = pbh_observable(A, C)
            logger.info("PBH done", extra={"pbh_pass": bool(pbh_pass)})

        # Gramians (infinite-horizon)
        gram_used = None
        gram_posdef = None
        gram_min_eig = None
        stability = None
        W_inf = None
        if req.do_gram:
            if discrete:
                stability = stable_dt(A)
                logger.debug("DT stability", extra={"stable": bool(stability)})
                W_inf = gramian_observability_dt(A, C) if stability else None
                if W_inf is not None:
                    gram_used = "DT"
            else:
                stability = stable_ct(A)
                logger.debug("CT stability", extra={"stable": bool(stability)})
                W_inf = gramian_observability_ct(A, C) if stability else None
                if W_inf is not None:
                    gram_used = "CT"
            if W_inf is not None:
                H = 0.5 * (W_inf + W_inf.conjugate().T)
                w, _ = eig(H)
                gram_min_eig = float(np.min(np.real(w)))
                tol_pd = req.tol if req.tol is not None else 1e-10
                gram_posdef = bool(gram_min_eig > tol_pd)
                logger.info("Gramian eig", extra={"gram_min_eig": float(gram_min_eig)})

        # Finite-horizon Gramians
        finite_used = None
        finite_horizon = None
        W_finite = None
        finite_min_eig = None
        if req.finite_dt is not None:
            finite_used = "DT"
            finite_horizon = float(int(req.finite_dt))
            W_finite = finite_gramian_dt(A, C, int(req.finite_dt))
            logger.debug("Finite DT gram computed", extra={"N": int(req.finite_dt)})
        if req.finite_ct is not None:
            finite_used = ("CT" if finite_used is None else finite_used + "+CT")
            finite_horizon = float(req.finite_ct)
            Wct = finite_gramian_ct(A, C, float(req.finite_ct))
            logger.debug("Finite CT gram computed", extra={"T": float(req.finite_ct)})
            W_finite = Wct if W_finite is None else (W_finite + Wct)
        if W_finite is not None:
            wfin, _ = eig(0.5 * (W_finite + W_finite.conjugate().T))
            finite_min_eig = float(np.min(np.real(wfin)))
            logger.info("Finite Gram min eig", extra={"finite_min_eig": float(finite_min_eig)})

        # Pretty text
        pretty_text = None
        if req.pretty:
            pretty_text = capture_pretty_text(
                discrete=discrete, n=n, m=C.shape[0], eigvals=[complex(z) for z in eigvals],
                Obsv=Obsv, rank=r_num, full=full_obsv, sym_rank=sym_rank,
                pbh_details=pbh_details, gram_used=gram_used, stability=stability,
                gram_min_eig=(gram_min_eig if gram_min_eig is not None else 0.0),
                gram_posdef=(bool(gram_posdef) if gram_posdef is not None else False),
                W_finite=W_finite, finite_used=finite_used, finite_horizon=finite_horizon,
                finite_min_eig=(finite_min_eig if finite_min_eig is not None else 0.0)
            )

        files: List[str] = []
        out_base = os.path.join(pkg_outdir(), req.name)

        # CSV saves
        if req.save_csv:
            np.savetxt(out_base + "_obsv.csv", np.real_if_close(Obsv), delimiter=",")
            files.append(out_base + "_obsv.csv")
            logger.debug("Saved CSV", extra={"path": out_base + "_obsv.csv"})
        if req.save_gram:
            if W_inf is not None:
                np.savetxt(out_base + "_gram_inf.csv", np.real_if_close(W_inf), delimiter=",")
                files.append(out_base + "_gram_inf.csv")
                logger.debug("Saved Gram(inf)", extra={"path": out_base + "_gram_inf.csv"})
            if W_finite is not None:
                np.savetxt(out_base + "_gram_finite.csv", np.real_if_close(W_finite), delimiter=",")
                files.append(out_base + "_gram_finite.csv")
                logger.debug("Saved Gram(finite)", extra={"path": out_base + "_gram_finite.csv"})

        # Minreal
        if req.do_minreal:
            Ar, Cr, T = minreal_observable(A, C, tol=req.tol)
            mr_path = out_base + "_minreal.json"
            save_json(mr_path, {
                "A_reduced": np.real_if_close(Ar).tolist(),
                "C_reduced": np.real_if_close(Cr).tolist(),
                "T_observable_basis": np.real_if_close(T).tolist(),
                "n_reduced": int(Ar.shape[0])
            })
            files.append(mr_path)
            logger.debug("Saved minreal", extra={"path": mr_path})

        # Summary JSON
        pbh_json = None
        if pbh_details is not None:
            pbh_json = [
                {
                    "lambda": [float(item["lambda"].real), float(item["lambda"].imag)],
                    "rank": int(item["rank"]),
                    "sigma_min": float(item["sigma_min"]),
                    "pass": bool(item["pass"]),
                }
                for item in pbh_details
            ]

        summary_obj = {
            "run_name": req.name,
            "discrete": bool(discrete),
            "n_states": int(n),
            "m_outputs": int(C.shape[0]),
            "rank_obsv": int(r_num),
            "full_obsv_rank_n": bool(full_obsv),
            "pbh_pass": (bool(pbh_pass) if pbh_pass is not None else None),
            "pbh": pbh_json,
            "stable": (bool(stability) if req.do_gram else None),
            "gramian_used": gram_used,
            "gramian_posdef": (bool(gram_posdef) if gram_posdef is not None else None),
            "gramian_min_eig": (float(gram_min_eig) if gram_min_eig is not None else None),
            "eigvals": [[float(z.real), float(z.imag)] for z in eigvals],
            "finite_used": finite_used,
            "finite_horizon": (float(finite_horizon) if finite_horizon is not None else None),
        }
        summary_json = json.dumps(summary_obj, indent=2)
        if req.save_json:
            path = out_base + "_summary.json"
            with open(path, "w") as f:
                f.write(summary_json)
            files.append(path)
            logger.debug("Saved summary", extra={"path": path})

        # Report text
        if req.report and pretty_text is not None:
            from .design import write_report
            write_report(req.report, pretty_text)
            files.append(req.report)
            logger.debug("Saved report", extra={"path": req.report})

        exit_code = 0 if full_obsv else 2
        logger.info("Finished ObservabilityApp.run", extra={"exit_code": int(exit_code)})
        return RunResult(exit_code=exit_code, summary_json=summary_json, files_written=files, stdout=pretty_text)
