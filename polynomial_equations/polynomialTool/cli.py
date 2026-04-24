#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys

# Allow running the CLI directly from inside the package folder
if __package__ in (None, ""):
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    from polynomial_equations.polynomialTool.apis import RunRequest
    from polynomial_equations.polynomialTool.app import PolynomialApp
    from polynomial_equations.polynomialTool.io import parse_coeffs
else:
    from .apis import RunRequest
    from .app import PolynomialApp
    from .io import parse_coeffs


def _add_common(p: argparse.ArgumentParser) -> None:
    """Arguments common to all subcommands."""
    p.add_argument("--A", required=True, help='Plant A(z⁻¹) coefficients in DESC order, e.g. "1,-2,1"')
    p.add_argument("--B", required=True, help='Plant B(z⁻¹) coefficients in DESC order, e.g. "0.02,0.02"')

    p.add_argument("--layout", choices=["ogata", "desc"], default="ogata",
                   help="Coefficient layout. 'ogata' builds the 2n×2n Sylvester from the book; "
                        "'desc' uses descending-power convolution blocks. (default: %(default)s)")
    p.add_argument("--d", type=int, default=0, help="Relative degree / input delay. (default: %(default)s)")
    p.add_argument("--degS", type=int, help="Override deg(S) (DESC layout).")
    p.add_argument("--degR", type=int, help="Override deg(R) (DESC layout).")

    # presentation
    p.add_argument("--pretty", action="store_true",
                   help="Pretty-print alpha/beta (sympy style) where applicable.")
    p.add_argument("--show_E", action="store_true",
                   help="Show the Sylvester matrix E when applicable.")

    # exports
    p.add_argument("--export_json", help="Export results to JSON file (relative 'out/...' resolved under package/out/).")
    p.add_argument("--export_csv", help="Export results to CSV file (relative 'out/...' resolved under package/out/).")

    # plotting/sim controls
    p.add_argument("--backend", choices=["mpl", "plotly", "none"], default="none",
                   help="Preview backend for step/ramp plots. (default: %(default)s)")
    p.add_argument("--save", help="Prefix path for saved plots/HTML (relative 'out/...' resolved under package/out/).")
    p.add_argument("--T", type=float, default=1.0, help="Sampling time for simulations. (default: %(default)s)")
    p.add_argument("--kmax", type=int, default=40, help="Simulation length in samples. (default: %(default)s)")

    # ogata parity handling (RST/model-match/polydesign paths that need it)
    p.add_argument("--ogata_parity", action="store_true",
                   help="Enable Ogata parity shift handling where supported.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="polynomialTool — Polynomial Equations (Ogata ch.7)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    # solve
    p_solve = sub.add_parser(
        "solve",
        help="Compute alpha/beta from A, B, D (Ogata or DESC).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    _add_common(p_solve)
    p_solve.add_argument("--D", required=True,
                         help='Right-hand-side polynomial D (DESC order), e.g. "1,0,0,0"')

    # polydesign
    p_pd = sub.add_parser(
        "polydesign",
        help="Closed-loop preview (step/ramp) using either D directly or (H,F,config).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    _add_common(p_pd)
    p_pd.add_argument("--D", help="Direct D polynomial (DESC). If omitted, must provide H,F and config.")
    p_pd.add_argument("--H", help="Closed-loop numerator H (DESC).")
    p_pd.add_argument("--F", help="Feedforward F (DESC).")
    p_pd.add_argument("--config", type=int, choices=[1, 2],
                      help="Controller configuration selector when using H and F.")

    # rst
    p_rst = sub.add_parser(
        "rst",
        help="RST design and preview.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    _add_common(p_rst)
    p_rst.add_argument("--H", required=True, help="Desired closed-loop numerator H (DESC).")
    p_rst.add_argument("--F", required=True, help="Feedforward F (DESC).")
    p_rst.add_argument("--rst_config", type=int, default=2, choices=[1, 2],
                       help="RST configuration selector.")

    # modelmatch
    p_mm = sub.add_parser(
        "modelmatch",
        help="Model matching with target G_model(z) and prefilter H1.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    _add_common(p_mm)
    p_mm.add_argument("--Gmodel_num", required=True, help="Target model numerator (DESC).")
    p_mm.add_argument("--Gmodel_den", required=True, help="Target model denominator (DESC).")
    p_mm.add_argument("--H1", required=True, help="Prefilter H1 (DESC).")
    p_mm.add_argument("--F", required=True, help="Feedforward F (DESC).")

    return ap


def _ns_to_req(cmd: str, ns: argparse.Namespace) -> RunRequest:
    # parse all polynomial vectors safely
    A = parse_coeffs(ns.A)
    B = parse_coeffs(ns.B)
    D = parse_coeffs(ns.D) if getattr(ns, "D", None) else None
    H = parse_coeffs(ns.H) if getattr(ns, "H", None) else None
    F = parse_coeffs(ns.F) if getattr(ns, "F", None) else None
    H1 = parse_coeffs(ns.H1) if getattr(ns, "H1", None) else None
    Gm_num = parse_coeffs(ns.Gmodel_num) if getattr(ns, "Gmodel_num", None) else None
    Gm_den = parse_coeffs(ns.Gmodel_den) if getattr(ns, "Gmodel_den", None) else None

    return RunRequest(
        mode=cmd,
        A=A,
        B=B,
        layout=ns.layout,
        d=ns.d,
        degS=ns.degS,
        degR=ns.degR,
        pretty=ns.pretty,
        show_E=getattr(ns, "show_E", False),
        export_json=getattr(ns, "export_json", None),
        export_csv=getattr(ns, "export_csv", None),
        backend=ns.backend,
        save=ns.save,
        T=ns.T,
        kmax=ns.kmax,
        D=D,
        H=H,
        F=F,
        config=getattr(ns, "config", None),
        ogata_parity=getattr(ns, "ogata_parity", False),
        Gmodel_num=Gm_num,
        Gmodel_den=Gm_den,
        H1=H1,
        rst_config=getattr(ns, "rst_config", 2),
    )


def main() -> None:
    parser = build_parser()
    ns = parser.parse_args()
    req = _ns_to_req(ns.cmd, ns)

    app = PolynomialApp()
    res = app.run(req)

    # Unified, compact stdout for alpha/beta if present
    if isinstance(res, dict) and "alpha" in res and "beta" in res:
        import numpy as np
        print("alpha:", np.round(res["alpha"], 12))
        print("beta :", np.round(res["beta"], 12))


if __name__ == "__main__":
    main()
