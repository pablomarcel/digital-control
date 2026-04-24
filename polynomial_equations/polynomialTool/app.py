from __future__ import annotations
from typing import Dict, Any, Tuple, List, Optional, Union

import numpy as np

from .apis import RunRequest
from .design import polydesign, rst_design, model_match, solve_alpha_beta
from .io import save_json, save_csv


def _pluck_alpha_beta_E(
    res: Union[Dict[str, Any], Tuple[Any, ...], List[Any]]
) -> Tuple[Optional[List[float]], Optional[List[float]], Optional[np.ndarray]]:
    """
    Normalize outputs coming from design.solve_alpha_beta:
      - If dict-like: expect keys 'alpha','beta','E' (E optional).
      - If tuple/list: assume (alpha, beta, E) or at least (alpha, beta).
    Returns (alpha, beta, E) where E may be None.
    """
    alpha = beta = None
    E: Optional[np.ndarray] = None

    if isinstance(res, dict):
        alpha = res.get("alpha")
        beta = res.get("beta")
        E = res.get("E")
    elif isinstance(res, (tuple, list)):
        if len(res) >= 2:
            alpha = res[0]
            beta = res[1]
        if len(res) >= 3:
            E = res[2]  # may be a numpy array
    return alpha, beta, E


def _export_solve_results_if_requested(
    req: RunRequest,
    alpha: Optional[List[float]],
    beta: Optional[List[float]],
):
    """
    For solve-mode only: write JSON/CSV if the caller requested it.
    We keep the payload minimal and stable: A, B, D, alpha, beta, layout.
    """
    if alpha is None or beta is None:
        return  # nothing to export

    if req.export_json:
        save_json(
            req.export_json,
            {
                "A": req.A,
                "B": req.B,
                "D": req.D,
                "alpha": alpha,
                "beta": beta,
                "layout": req.layout,
            },
        )
    if req.export_csv:
        # CSV rows match the simple convention (name, coeff_descending)
        rows = [("A", req.A), ("B", req.B), ("D", req.D), ("alpha", alpha), ("beta", beta)]
        save_csv(req.export_csv, rows)


class PolynomialApp:
    def run(self, req: RunRequest) -> Dict[str, Any]:
        """
        Dispatch entry-point for the polynomialTool app.

        Modes:
          - 'solve'      -> solve_alpha_beta (and optionally export/print E)
          - 'polydesign' -> polydesign (handles its own exports/plots)
          - 'rst'        -> rst_design     (handles its own exports/plots)
          - 'modelmatch' -> model_match    (handles its own exports/plots)
        """
        if req.mode == "solve":
            if req.D is None:
                raise ValueError("solve mode requires D")

            res = solve_alpha_beta(
                req.A, req.B, req.D, req.d, req.degS, req.degR, req.layout
            )

            # Try to pull alpha, beta, E out of the return (dict or tuple)
            alpha, beta, E = _pluck_alpha_beta_E(res)

            # Optional: show Sylvester matrix if requested and available
            if req.show_E and E is not None:
                np.set_printoptions(precision=6, suppress=True)
                print("\nSylvester E:\n", E)

            # Optional: export JSON/CSV (solve-mode only)
            _export_solve_results_if_requested(req, alpha, beta)

            # Preserve original return value so existing code/tests keep working
            return res  # type: ignore[return-value]

        if req.mode == "polydesign":
            # polydesign already handles exporting/plotting internally
            return polydesign(
                req.A,
                req.B,
                req.D,
                req.H,
                req.F,
                req.d,
                req.degS,
                req.degR,
                req.layout,
                req.pretty,
                req.show_E,
                req.backend,
                req.save,
                req.T,
                req.kmax,
                req.config,
                req.export_json,
                req.export_csv,
                req.ogata_parity,
            )

        if req.mode == "rst":
            if req.H is None or req.F is None:
                raise ValueError("rst mode requires H and F")
            return rst_design(
                req.A,
                req.B,
                req.H,
                req.F,
                req.d,
                req.degS,
                req.degR,
                req.layout,
                req.rst_config,
                req.backend,
                req.save,
                req.T,
                req.kmax,
                req.export_json,
                req.pretty,
                req.ogata_parity,
            )

        if req.mode == "modelmatch":
            if (
                req.Gmodel_num is None
                or req.Gmodel_den is None
                or req.H1 is None
                or req.F is None
            ):
                raise ValueError(
                    "modelmatch requires Gmodel_num, Gmodel_den, H1, F"
                )
            return model_match(
                req.A,
                req.B,
                req.Gmodel_num,
                req.Gmodel_den,
                req.H1,
                req.F,
                req.d,
                req.degS,
                req.degR,
                req.layout,
                req.backend,
                req.save,
                req.T,
                req.kmax,
                req.export_json,
                req.pretty,
            )

        raise ValueError(f"Unknown mode: {req.mode}")
