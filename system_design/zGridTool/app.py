# -*- coding: utf-8 -*-
"""
App orchestration for zGridTool.
"""
from __future__ import annotations
import logging, math
from typing import List
from pathlib import Path

from .apis import RunRequest, RunResult
from .io import resolve_overlay_paths, read_pz_any
from .utils import ensure_out_path, log_call
from .design import draw_mpl, draw_plotly, Style
from .io import pretty_list

def _compose_title(base: str, T: float, zetas: List[float], wd_over_ws: List[float], wnT: List[float],
                   mode: str, backend: str) -> str:
    if mode == "auto":
        mode = "full" if backend == "mpl" else "minimal"
    if mode == "full":
        return f"{base}  (T={T:g}s, ζ={pretty_list(zetas)}, ωd/ωs={pretty_list(wd_over_ws)}, ωnT={pretty_list(wnT)})"
    return f"{base}  (T={T:g}s)"

class ZGridApp:
    def __init__(self):
        self.log = logging.getLogger(self.__class__.__name__)

    @log_call
    def run(self, req: RunRequest) -> RunResult:
        logging.basicConfig(level=logging.DEBUG if req.verbose else logging.INFO,
                            format="%(levelname)s: %(message)s")
        T = 1.0/req.fs if (req.fs and req.fs>0) else float(req.T if req.T else 1.0)
        pzs = []
        for p in resolve_overlay_paths(req.pz_files):
            if not p.exists():
                self.log.warning("Overlay file not found: %s", p)
                continue
            self.log.info("Reading overlay: %s", p)
            pzs.extend(read_pz_any(p))

        title = _compose_title(req.title, T, req.zetas, req.wd_over_ws, req.wnT, req.title_mode, req.backend)
        export_prefix = ensure_out_path(req.export_csv_prefix) if req.export_csv_prefix else None

        res = RunResult(csv_prefix=str(export_prefix) if export_prefix else None)

        if req.backend == "mpl":
            fig = draw_mpl(T=T, zetas=req.zetas, wd_over_ws=req.wd_over_ws, wnT=req.wnT,
                           theta_max=req.theta_max, settling_sigma=req.settling_sigma,
                           pzs=pzs, style=Style(), width=req.width, height=req.height, dpi=req.dpi,
                           dark=req.dark, title=title, export_prefix=export_prefix)
            png_path = ensure_out_path(req.png)
            assert png_path is not None
            png_path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(png_path, dpi=req.dpi, bbox_inches="tight")
            res.png_path = str(png_path)
        else:
            fig = draw_plotly(T=T, zetas=req.zetas, wd_over_ws=req.wd_over_ws, wnT=req.wnT,
                              theta_max=req.theta_max, settling_sigma=req.settling_sigma,
                              pzs=pzs, title=title, width=req.width, height=req.height,
                              legend_mode=req.legend_mode, legend_loc=req.legend_loc,
                              responsive=req.responsive, theme=req.theme)
            html_name = req.plotly_html or "zgrid.html"
            html_path = ensure_out_path(html_name)
            assert html_path is not None
            html_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                fig.write_html(str(html_path), include_plotlyjs="cdn",
                               full_html=True, config=dict(responsive=True))
            except TypeError:
                fig.write_html(str(html_path), include_plotlyjs="cdn", full_html=True)
            res.html_path = str(html_path)
            try:
                # best-effort PNG via kaleido if available
                png_path = ensure_out_path(req.png)
                assert png_path is not None
                fig.write_image(str(png_path), width=req.width, height=req.height, scale=1.0)
                res.png_path = str(png_path)
            except Exception:
                self.log.info("PNG export via Plotly skipped (kaleido not installed).")

        return res
