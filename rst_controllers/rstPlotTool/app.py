from __future__ import annotations
import math, os, glob
from typing import List, Dict, Optional, Tuple
import numpy as np

from .apis import RunRequest
from .io import expand_files, load_csv, load_design_json
from .core import crop_by_k, step_metrics
from .design import mpl_overlay, mpl_single, plotly_overlay, plotly_single

class RSTPlotApp:
    """High-level orchestrator for plotting RST step-response CSVs."""

    def run(self, req: RunRequest) -> None:
        files_all = expand_files(req.files)
        overlay = req.overlay if req.overlay is not None else (len(files_all) > 1)

        # include/exclude filters (use module-level imports to avoid UnboundLocalError)
        files = files_all
        if req.filters.include:
            files = [f for f in files if len(glob.fnmatch.filter([os.path.basename(f)], req.filters.include)) > 0]
        if req.filters.exclude:
            files = [f for f in files if len(glob.fnmatch.filter([os.path.basename(f)], req.filters.exclude)) == 0]

        if len(files) == 0:
            print("[error] no input files after include/exclude filtering.")
            return

        ylims = (
            tuple(req.ylimits.ylimY) if req.ylimits.ylimY else None,
            tuple(req.ylimits.ylimU) if req.ylimits.ylimU else None,
            tuple(req.ylimits.ylimE) if req.ylimits.ylimE else None,
        )

        if overlay and len(files) > 1:
            datasets = [crop_by_k(load_csv(f), req.kmin, req.kmax) for f in files]
            # quick metrics print
            for f, d in zip(files, datasets):
                met = step_metrics(d["k"], d["r"], d["y"])
                print(f"{os.path.basename(f):<16} →  final y={met['yf']:.6g}, "
                      f"final e={met['ef']:.6g}, overshoot={met['overshoot']:.3g}%, "
                      f"trise={met['trise'] if not math.isnan(met['trise']) else 'n/a'}, "
                      f"tsettle={met['tsettle'] if not math.isnan(met['tsettle']) else 'n/a'}")

            title = req.title or "RST Step — Overlay"
            if req.backend in ("both", "mpl"):
                mpl_overlay("plot_overlay_mpl.png", files, datasets, req.style, req.dpi,
                            legend_mode=("none" if req.legend == "none" else req.legend),
                            robust=req.robust, ylims=ylims, clip_to_limits=req.clip, title=title)
                print("[matplotlib] saved: rst_controllers/rstPlotTool/out/plot_overlay_mpl.png")
            if req.backend in ("both", "plotly"):
                plotly_overlay("plot_overlay_plotly.html", files, datasets, req.style,
                               legend_mode=("full" if req.legend == "full" else "compact"),
                               robust=req.robust, ylims=ylims, title=title)
                print("[plotly] saved: rst_controllers/rstPlotTool/out/plot_overlay_plotly.html")
            return

        # single-run mode
        for f in files:
            d = crop_by_k(load_csv(f), req.kmin, req.kmax)
            met = step_metrics(d["k"], d["r"], d["y"])
            print(f"{os.path.basename(f)}  →  final y={met['yf']:.6g}, "
                  f"final u={float(d['u'][-1]):.6g}, final e={met['ef']:.6g}, "
                  f"overshoot={met['overshoot']:.3g}%, trise="
                  f"{met['trise'] if not math.isnan(met['trise']) else 'n/a'}, "
                  f"tsettle={met['tsettle'] if not math.isnan(met['tsettle']) else 'n/a'}")

            design = load_design_json(req.annotate) if req.annotate else None
            if req.title:
                title = req.title
            elif design:
                A = design["plant"]["A"]; B = design["plant"]["B"]; dly = design["plant"]["d"]
                Acl = design["target"]["Acl"]
                title = f"RST Step: A={A}, B={B}, d={dly}, Acl={Acl}"
            else:
                title = f"RST Step: {os.path.basename(f)}"

            stem = os.path.splitext(os.path.basename(f))[0]

            if req.backend in ("both", "mpl"):
                mpl_single(f"{stem}_mpl.png", d, title, req.style, req.dpi, ylims, annotate=design)
                print(f"[matplotlib] saved: rst_controllers/rstPlotTool/out/{stem}_mpl.png")
            if req.backend in ("both", "plotly"):
                plotly_single(f"{stem}_plotly.html", d, title, req.style, ylims, annotate=design)
                print(f"[plotly] saved: rst_controllers/rstPlotTool/out/{stem}_plotly.html")
