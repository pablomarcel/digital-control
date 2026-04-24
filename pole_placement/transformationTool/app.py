
from __future__ import annotations
from typing import List
import numpy as np

from .apis import RunRequest, TransformResult
from .core import (
    to_ccf, to_ocf, to_diag, to_jordan_sympy, siso_tf_coeffs,
    controllability_matrix, observability_matrix
)
from .design import print_header, show_matrix_block, export_bundle

class TransformationApp:
    def run(self, req: RunRequest) -> List[TransformResult]:
        A, B, C, D = req.A, req.B, req.C, req.D
        eigs = [complex(x) for x in np.linalg.eigvals(A)]
        results: List[TransformResult] = []

        # Optional SISO TF info
        if req.show_tf and B is not None and C is not None and B.shape[1] == 1 and C.shape[0] == 1:
            b, a = siso_tf_coeffs(A, B, C, D)
            print_header("SISO transfer coefficients (G)")
            print(f"a (den excl. leading 1): {np.real_if_close(a)}")
            print(f"b (num): {np.real_if_close(b)}")

        # CCF
        if req.to_ccf:
            print_header("Controllable Canonical Form (CCF)")
            Ahat, Bhat, Chat, Dhat, T, a = to_ccf(A, B, C, D)
            show_matrix_block(Ahat, Bhat, Chat, Dhat, req.pretty)
            res = TransformResult(
                name=req.name + "_ccf", form="ccf", eigvals=eigs, T=T,
                Ahat=Ahat, Bhat=Bhat, Chat=Chat, Dhat=Dhat, a_coeffs=[complex(x) for x in a]
            )
            if req.check_invariance and (B is not None) and (C is not None):
                res.rank_ctrb_before = int(np.linalg.matrix_rank(controllability_matrix(A, B)))
                res.rank_ctrb_after  = int(np.linalg.matrix_rank(controllability_matrix(Ahat, Bhat)))
                res.rank_obsv_before = int(np.linalg.matrix_rank(observability_matrix(A, C)))
                res.rank_obsv_after  = int(np.linalg.matrix_rank(observability_matrix(Ahat, Chat)))
                print(f"rank ctrb before/after: {res.rank_ctrb_before}/{res.rank_ctrb_after}")
                print(f"rank obsv  before/after: {res.rank_obsv_before}/{res.rank_obsv_after}")
            export_bundle(res.name, T, Ahat, Bhat, Chat, Dhat, req.save_json, req.save_csv)
            results.append(res)

        # OCF
        if req.to_ocf:
            print_header("Observable Canonical Form (OCF)")
            Ahat, Bhat, Chat, Dhat, Q, a = to_ocf(A, B, C, D)
            show_matrix_block(Ahat, Bhat, Chat, Dhat, req.pretty)
            res = TransformResult(
                name=req.name + "_ocf", form="ocf", eigvals=eigs, T=Q,
                Ahat=Ahat, Bhat=Bhat, Chat=Chat, Dhat=Dhat, a_coeffs=[complex(x) for x in a]
            )
            if req.check_invariance and (B is not None) and (C is not None):
                res.rank_ctrb_before = int(np.linalg.matrix_rank(controllability_matrix(A, B)))
                res.rank_ctrb_after  = int(np.linalg.matrix_rank(controllability_matrix(Ahat, Bhat))) if Bhat is not None else None
                res.rank_obsv_before = int(np.linalg.matrix_rank(observability_matrix(A, C)))
                res.rank_obsv_after  = int(np.linalg.matrix_rank(observability_matrix(Ahat, Chat))) if Chat is not None else None
                print(f"rank ctrb before/after: {res.rank_ctrb_before}/{res.rank_ctrb_after}")
                print(f"rank obsv  before/after: {res.rank_obsv_before}/{res.rank_obsv_after}")
            export_bundle(res.name, Q, Ahat, Bhat, Chat, Dhat, req.save_json, req.save_csv)
            results.append(res)

        # Diagonal
        if req.to_diag:
            print_header("Diagonal Canonical Form")
            Ahat, Bhat, Chat, Dhat, P = to_diag(A, B, C, D)
            show_matrix_block(Ahat, Bhat, Chat, Dhat, req.pretty)
            res = TransformResult(
                name=req.name + "_diag", form="diag", eigvals=eigs, T=P,
                Ahat=Ahat, Bhat=Bhat, Chat=Chat, Dhat=Dhat
            )
            export_bundle(res.name, P, Ahat, Bhat, Chat, Dhat, req.save_json, req.save_csv)
            results.append(res)

        # Jordan
        if req.to_jordan:
            print_header("Jordan Canonical Form (SymPy)")
            J, Bhat, Chat, Dhat, S = to_jordan_sympy(A, B, C, D)
            show_matrix_block(J, Bhat, Chat, Dhat, req.pretty)
            res = TransformResult(
                name=req.name + "_jordan", form="jordan", eigvals=eigs, T=S,
                Ahat=J, Bhat=Bhat, Chat=Chat, Dhat=Dhat
            )
            export_bundle(res.name, S, J, Bhat, Chat, Dhat, req.save_json, req.save_csv)
            results.append(res)

        if not (req.to_ccf or req.to_ocf or req.to_diag or req.to_jordan):
            raise SystemExit("Choose at least one transform: --to-ccf/--to-ocf/--to-diag/--to-jordan")

        return results
