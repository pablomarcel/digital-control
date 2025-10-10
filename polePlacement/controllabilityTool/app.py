from __future__ import annotations
import os, json, logging
from typing import Any, Dict, Optional, List, Tuple
import numpy as np
from numpy.linalg import eig

from .apis import RunRequest, RunResult
from .io import load_from_json, parse_matrix_string
from .core import (
    controllability_matrix, output_controllability_matrix, pbh_controllable,
    gramian_controllability_ct, gramian_controllability_dt, finite_gramian_ct,
    finite_gramian_dt, minreal_controllable, sympy_rank_ctrb
)
from .utils import ensure_out_dir, stable_ct, stable_dt, rank_numeric
from .design import fmt_matrix, write_csv, write_json, write_text

logger = logging.getLogger(__name__)

class ControllabilityApp:
    def _load(self, req: RunRequest):
        logger.debug("Loading system from %s", ("JSON:"+str(req.json_path)) if req.json_path else "CLI strings")
        if req.json_path:
            A, B, disc_flag, C, D = load_from_json(req.json_path)
            discrete = bool(req.discrete or disc_flag)
        else:
            if not req.A or not req.B:
                raise SystemExit("Error: A and B are required when not using JSON.")
            A = parse_matrix_string(req.A)
            B = parse_matrix_string(req.B)
            C = parse_matrix_string(req.C) if req.C else None
            D = parse_matrix_string(req.D) if req.D else None
            discrete = bool(req.discrete)
        logger.debug("Loaded shapes A%s, B%s, C%s, D%s, discrete=%s",
                     getattr(A,'shape',None), getattr(B,'shape',None),
                     getattr(C,'shape',None), getattr(D,'shape',None), discrete)
        return A, B, C, D, discrete

    def run(self, req: RunRequest) -> RunResult:
        # Configure default logging if user didn't set it
        if not logging.getLogger().handlers:
            logging.basicConfig(level=getattr(logging, req.log.upper(), logging.INFO),
                                format="%(levelname)s %(name)s: %(message)s")
        logger.info("=== ControllabilityApp.run start ===")
        logger.info("RunRequest: %s", req)

        ensure_out_dir(os.path.join(os.path.dirname(__file__), "out"))
        # Load
        A, B, C, D, discrete = self._load(req)
        n = A.shape[0]
        if A.shape[0] != A.shape[1]:
            raise SystemExit("Error: A must be square.")
        if B.shape[0] != n:
            raise SystemExit(f"Error: B must have {n} rows to match A.")
        logger.debug("n=%d, inputs r=%d", n, B.shape[1])

        # State ctrb
        Ctrb = controllability_matrix(A, B, horizon=req.horizon)
        r_num = rank_numeric(Ctrb, tol=req.tol)
        full_ctrb = (r_num == n)
        eigvals, _ = eig(A)
        logger.debug("rank(Ctrb)=%d (full=%s), eig(A)=%s", r_num, full_ctrb, [complex(z) for z in eigvals])

        pbh_pass = None
        pbh_details = None
        if req.pbh:
            pbh_pass, pbh_details = pbh_controllable(A, B)
            logger.debug("PBH pass=%s, details=%s", pbh_pass, pbh_details)

        gram_used = None
        gram_posdef = None
        gram_min_eig = None
        W_inf = None
        if req.gram:
            logger.debug("Computing infinite-horizon Gramian (discrete=%s)", discrete)
            if discrete:
                W_inf = gramian_controllability_dt(A, B)
                if W_inf is not None:
                    gram_used = "DT"
            else:
                W_inf = gramian_controllability_ct(A, B)
                if W_inf is not None:
                    gram_used = "CT"
            if W_inf is not None:
                H = 0.5 * (W_inf + W_inf.conj().T)
                w, _ = eig(H)
                gram_min_eig = float(np.min(np.real(w)))
                tol_pd = req.tol if req.tol is not None else 1e-10
                gram_posdef = bool(gram_min_eig > tol_pd)
                logger.debug("Gramian type=%s, min_eig≈%.3e, PD=%s", gram_used, gram_min_eig, gram_posdef)
            else:
                logger.debug("Gramian not computed (likely unstable or backend unavailable)")

        finite_used = None
        finite_horizon = None
        W_finite = None
        if req.finite_dt is not None:
            finite_used = "DT"
            finite_horizon = float(int(req.finite_dt))
            W_finite = finite_gramian_dt(A, B, int(req.finite_dt))
            logger.debug("Finite DT Gramian N=%d computed", int(req.finite_dt))
        if req.finite_ct is not None:
            finite_used = ("CT" if finite_used is None else finite_used + "+CT")
            finite_horizon = float(req.finite_ct)
            Wct = finite_gramian_ct(A, B, float(req.finite_ct))
            W_finite = Wct if W_finite is None else (W_finite + Wct)
            logger.debug("Finite CT Gramian T=%.3g computed; combined=%s", float(req.finite_ct), finite_used)

        sym_rank = sympy_rank_ctrb(A, B, req.horizon) if req.symbolic else None
        if req.symbolic:
            logger.debug("SymPy rank(Ctrb)=%s", sym_rank)

        # Output controllability
        out_rank = None
        out_full = None
        c_row_rank = None
        outM = None
        if req.output_ctrb:
            logger.debug("Output controllability requested")
            if C is None:
                raise SystemExit("Error: output-ctrb requires C (optional D).")
            if C.shape[1] != n:
                raise SystemExit(f"Error: C must have {n} columns to match A.")
            if D is not None and D.shape[0] != C.shape[0]:
                raise SystemExit(f"Error: D must have {C.shape[0]} rows to match C.")
            outM = output_controllability_matrix(A, B, C, horizon=req.horizon, D=D)
            out_rank = rank_numeric(outM, tol=req.tol)
            m = C.shape[0]
            out_full = bool(out_rank == m)
            c_row_rank = int(rank_numeric(C, tol=req.tol))
            logger.debug("Output rank=%s (m=%d), rank(C)=%d", out_rank, m, c_row_rank)

        # Pretty print
        if req.pretty:
            print("\n=== Controllability (Ogata) ===")
            print(f"System type: {'discrete-time' if discrete else 'continuous-time'}")
            print(f"n (states) = {n}, r (inputs) = {B.shape[1]}")
            print("Eigenvalues(A):", [complex(z) for z in eigvals])
            print("\nCtrb = [B, AB, ..., A^{n-1}B]")
            print(fmt_matrix(Ctrb))
            print(f"\nrank(Ctrb) = {r_num}  ->  {'CONTROLLABLE ✅' if full_ctrb else 'NOT controllable ❌'}")
            if sym_rank is not None:
                print(f"rank(Ctrb) [SymPy exact] = {sym_rank}")
            if req.pbh and pbh_details is not None:
                print("\nPBH test: rank([λI - A, B]) = n for all eigenvalues λ.")
                for item in pbh_details:
                    lam = item["lambda"]
                    print(f"  λ={lam:>12}  rank={item['rank']:>2}  σ_min={item['sigma_min']:.3e}  "
                          f"{'OK' if item['pass'] else 'FAIL'}")
            if req.gram:
                print("\nInfinite-horizon Gramian:")
                if W_inf is None:
                    print("  Not computed (system not stable or unavailable).")
                else:
                    print(f"  type={gram_used}, min eig ≈ {gram_min_eig:.3e}, "
                          f"{'PD ✅' if gram_posdef else 'not PD ❌'}")
            if W_finite is not None:
                from numpy.linalg import eig as la_eig
                wfin, _ = la_eig(0.5 * (W_finite + W_finite.conj().T))
                print(f"\nfinite-horizon Gramian ({finite_used}, horizon={finite_horizon}), "
                      f"min eig ≈ {float(np.min(np.real(wfin))):.3e}")

            if req.output_ctrb and outM is not None:
                print("\n=== Output controllability ===")
                m = C.shape[0]
                print(f"m (outputs) = {m}, rank(C) = {c_row_rank}{' (full row rank)' if c_row_rank==m else ''}")
                tag = "[ D : C B : C A B : ... ]" if D is not None else "[ C B : C A B : ... ]"
                print(f"{tag}")
                print(fmt_matrix(outM))
                print(f"\nrank(output matrix) = {out_rank}  "
                      f"->  {'OUTPUT-CONTROLLABLE ✅' if out_full else 'NOT output-controllable ❌'}")

        # Persist
        base = os.path.join(os.path.dirname(__file__), "out", req.name)
        if req.save_csv:
            write_csv(base + "_ctrb.csv", np.real_if_close(Ctrb))
            logger.debug("Saved %s_ctrb.csv", base)
        if req.save_gram:
            if W_inf is not None:
                write_csv(base + "_gram_inf.csv", np.real_if_close(W_inf))
            if W_finite is not None:
                write_csv(base + "_gram_finite.csv", np.real_if_close(W_finite))
            logger.debug("Saved gramian CSVs (as available) for base=%s", base)
        if req.output_ctrb and req.save_output_csv and outM is not None:
            write_csv(base + "_outctrb.csv", np.real_if_close(outM))
            logger.debug("Saved %s_outctrb.csv", base)

        if req.minreal:
            Ar, Br, Tc = minreal_controllable(A, B, tol=req.tol)
            mr_path = os.path.join(os.path.dirname(__file__), "out", f"{req.name}_minreal.json")
            write_json(mr_path, {
                "A_reduced": np.real_if_close(Ar).tolist(),
                "B_reduced": np.real_if_close(Br).tolist(),
                "T_controllable_basis": np.real_if_close(Tc).tolist(),
                "n_reduced": int(Ar.shape[0])
            })
            if req.pretty:
                print(f"\nMinimal realization saved to {mr_path}")
            logger.debug("Minimal realization written to %s", mr_path)

        summary = {
            "name": req.name,
            "discrete": bool(discrete),
            "n_states": int(n),
            "r_inputs": int(B.shape[1]),
            "rank_ctrb": int(r_num),
            "full_ctrb_rank_n": bool(r_num == n),
            "pbh_pass": (bool(pbh_pass) if pbh_pass is not None else None),
            "pbh": pbh_details,
            "stable": (bool(stable_dt(A) if discrete else stable_ct(A)) if req.gram else None),
            "gramian_used": gram_used,
            "gramian_posdef": (bool(gram_posdef) if gram_posdef is not None else None),
            "gramian_min_eig": (float(gram_min_eig) if gram_min_eig is not None else None),
            "eigvals": [[float(z.real), float(z.imag)] for z in eigvals],
            "finite_used": finite_used,
            "finite_horizon": finite_horizon,
            "output_rank": (int(out_rank) if out_rank is not None else None),
            "output_full_rank_m": (bool(out_full) if out_full is not None else None),
            "c_row_rank": (int(c_row_rank) if c_row_rank is not None else None),
            "d_present": (D is not None if req.output_ctrb else None),
        }

        # JSON-safe PBH conversion
        if summary.get("pbh") is not None:
            safe_pbh: List[Dict[str, Any]] = []
            for item in summary["pbh"]:
                safe_pbh.append({
                    "lambda": [float(item["lambda"].real), float(item["lambda"].imag)],
                    "rank": int(item["rank"]),
                    "sigma_min": float(item["sigma_min"]),
                    "pass": bool(item["pass"]),
                })
            summary["pbh"] = safe_pbh

        summary_json = json.dumps(summary, indent=2)
        if req.save_json:
            write_text(base + "_summary.json", summary_json)
            logger.debug("Saved summary JSON to %s_summary.json", base)

        logger.info("=== ControllabilityApp.run end (exit=%s) ===", 0 if full_ctrb else 2)
        return RunResult(exit_code=0 if full_ctrb else 2, summary_json=summary_json)
