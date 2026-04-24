#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import os
import sys

# ---------- Import shim so `python cli.py` works with absolute imports ----------
if __package__ in (None, ""):
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    from rst_controllers.rstPlotTool.apis import RunRequest, YLimits, OverlayFilters
    from rst_controllers.rstPlotTool.app import RSTPlotApp
else:
    from .apis import RunRequest, YLimits, OverlayFilters
    from .app import RSTPlotApp

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="rst_controllers.rstPlotTool",
        description="Plot RST step-response CSVs (from rst.py) with matplotlib and/or Plotly.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("files", nargs="+", help="CSV file(s) or globs (e.g., out/*.csv)")
    p.add_argument("--overlay", dest="overlay", action="store_true", help="Plot all inputs on a single figure.")
    p.add_argument("--no-overlay", dest="overlay", action="store_false", help="Plot each input separately.")
    p.set_defaults(overlay=None)

    p.add_argument("--backend", choices=["both", "mpl", "plotly"], default="both", help="Which backend(s) to render.")
    p.add_argument("--style", choices=["matlab", "light", "dark"], default="matlab", help="Plot style.")
    p.add_argument("--dpi", type=int, default=150, help="Matplotlib DPI")

    p.add_argument("--kmin", type=float, help="Min k for plotting")
    p.add_argument("--kmax", type=float, help="Max k for plotting")
    p.add_argument("--robust", type=float, default=0.995, help="Overlay y-limits from central quantiles (1.0 disables robust clipping).")
    p.add_argument("--ylimY", nargs=2, type=float, metavar=("YMIN", "YMAX"), help="Explicit y-limits for r/y subplot.")
    p.add_argument("--ylimU", nargs=2, type=float, metavar=("UMIN", "UMAX"), help="Explicit y-limits for u subplot.")
    p.add_argument("--ylimE", nargs=2, type=float, metavar=("EMIN", "EMAX"), help="Explicit y-limits for e subplot.")
    p.add_argument("--clip", action="store_true", help="Clip traces to the chosen y-limits (helps with unstable overlays).")

    p.add_argument("--legend", choices=["compact", "full", "none"], default="compact", help="Legend mode in overlay.")
    p.add_argument("--include", help="Only include files matching this glob (applied after positionals).")
    p.add_argument("--exclude", help="Exclude files matching this glob.")

    p.add_argument("--annotate", help="Design JSON (…_design.json) to show in the plot (single-run).")
    p.add_argument("--title", help="Override figure title")
    return p

def args_to_request(ns: argparse.Namespace) -> RunRequest:
    ylims = YLimits(
        ylimY=tuple(ns.ylimY) if ns.ylimY else None,
        ylimU=tuple(ns.ylimU) if ns.ylimU else None,
        ylimE=tuple(ns.ylimE) if ns.ylimE else None,
    )
    filters = OverlayFilters(include=ns.include, exclude=ns.exclude)
    return RunRequest(
        files=list(ns.files),
        overlay=ns.overlay,
        backend=ns.backend,
        style=ns.style,
        dpi=ns.dpi,
        kmin=ns.kmin, kmax=ns.kmax,
        robust=ns.robust,
        ylimits=ylims,
        clip=ns.clip,
        legend=ns.legend,
        filters=filters,
        annotate=ns.annotate,
        title=ns.title,
    )

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    app = RSTPlotApp()
    app.run(args_to_request(ns))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
