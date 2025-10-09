from __future__ import annotations
from dataclasses import asdict
from typing import Dict, Any
import numpy as np
from .apis import RunRequest
from .io import parse_matrix, parse_poles, load_json_ABC, safe_scalar
from .core import (
    ackermann_siso, eigenvector_method_siso, place_method,
    compute_K0, simulate_step, ctrb, obsv, pretty_poly_from_roots, match_pole_sets
)
from .design import save_json, save_csv_step, plot_step
from .utils import ensure_out_dir, to_real_if_close, mat_to_str

class PolePlacementApp:
    """High-level orchestration of pole placement design, simulation, plotting & exports."""

    def __init__(self):
        pass

    def _resolve_ABC(self, req: RunRequest):
        if req.json_in:
            return load_json_ABC(req.json_in)
        A = parse_matrix(req.A)
        B = parse_matrix(req.B)
        C = parse_matrix(req.C)
        if A is None or B is None or C is None:
            raise ValueError("Provide A, B and C (or json_in).")
        return A, B, C

    def _resolve_poles(self, req: RunRequest, n: int):
        if req.deadbeat:
            return np.zeros(n, dtype=complex)
        if not req.poles:
            raise ValueError("Provide poles or set deadbeat=True.")
        return parse_poles(req.poles, n)

    def _resolve_method(self, req: RunRequest, r: int) -> str:
        m = (req.method or "auto").lower()
        if m == "auto":
            return "ackermann" if r == 1 else "place"
        return m

    def _compute_K(self, method: str, A, B, poles):
        if method == "ackermann":
            if B.shape[1] != 1:
                return place_method(A, B, poles), "PLACE"
            return ackermann_siso(A, B, poles), "ACKERMANN"
        if method == "ogata":
            if B.shape[1] != 1:
                return place_method(A, B, poles), "PLACE"
            return eigenvector_method_siso(A, B, poles), "OGATA (eigs)"
        if method == "eigs":
            return eigenvector_method_siso(A, B, poles), "EIGS"
        if method == "place":
            return place_method(A, B, poles), "PLACE"
        raise ValueError(f"Unknown method: {method}")

    def run(self, req: RunRequest) -> Dict[str, Any]:
        A, B, C = self._resolve_ABC(req)
        n = A.shape[0]
        r = B.shape[1]

        poles = self._resolve_poles(req, n)

        a_open = pretty_poly_from_roots(np.linalg.eigvals(A))
        a_des  = pretty_poly_from_roots(poles)

        method = self._resolve_method(req, r)
        K, resolved = self._compute_K(method, A, B, poles)
        Acl = A - B @ K
        ev_cl = np.linalg.eigvals(Acl)
        place_err = match_pole_sets(ev_cl, poles)

        # K0 & S
        K0, S, k0_status = compute_K0(Acl, B, C)

        # Simulate
        kgrid, y = simulate_step(A, B, C, K, K0, N=req.samples)

        # Exports
        outdir = ensure_out_dir(override=req.outdir)
        plot_file = None
        if req.plot != "none":
            plot_file = (outdir / f"{req.name}_step_mpl.png") if req.plot == "mpl" else (outdir / f"{req.name}_step_plotly.html")
            plot_step(kgrid, y, req.plot, req.style, plot_file)

        csv_file = None
        if req.save_csv:
            csv_file = save_csv_step(kgrid, y, outdir, req.name)

        json_file = None
        if req.save_json:
            summary = dict(
                method=resolved,
                A=A.tolist(), B=B.tolist(), C=C.tolist(),
                open_loop_poly=a_open, desired_poly=a_des,
                desired_poles=[safe_scalar(v) for v in poles],
                K=K.tolist(),
                Acl_eigs=[safe_scalar(v) for v in ev_cl],
                placement_error=place_err,
                S=None if k0_status!="ok" else S.tolist(),
                K0=K0.tolist(),
                samples=req.samples,
                plot_backend=req.plot, plot_style=req.style,
                plot_file=str(plot_file) if plot_file else None,
                name=req.name
            )
            json_file = save_json(summary, outdir, req.name)

        return {
            "resolved_method": resolved,
            "K": K, "K0": K0, "Acl_eigs": ev_cl, "placement_error": place_err,
            "plot_file": plot_file, "csv_file": csv_file, "json_file": json_file,
            "outdir": outdir,
        }
