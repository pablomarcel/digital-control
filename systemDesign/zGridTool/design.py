# -*- coding: utf-8 -*-
"""
Rendering and CSV export.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import math, logging
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from .core import spiral_const_zeta, curve_const_wnT, ray_theta, ring_points
from .io import PZ
from .utils import ensure_out_path, log_call

# Plotly is optional
try:
    import plotly.graph_objects as go
    _PLOTLY_OK = True
except Exception:
    _PLOTLY_OK = False

@dataclass
class Style:
    zeta_color: str = "#1f77b4"
    wn_color:   str = "#2ca02c"
    ray_color:  str = "#ff7f0e"
    pole_color: str = "#d62728"
    zero_edge:  str = "#1f77b4"
    zero_face:  str = "#ffffff"

def _write_csv(path: Path, header: List[str], rows: List[List[float]], append: bool=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append and path.exists() else "w"
    import csv
    with path.open(mode, newline="") as f:
        w = csv.writer(f)
        if mode == "w":
            w.writerow(header)
        for r in rows:
            w.writerow(r)

def _export_curve(prefix: Path, tag: str, x: np.ndarray, y: np.ndarray):
    path = prefix.with_name(prefix.name + f"_{tag}.csv")
    _write_csv(path, ["x","y"], [[float(a), float(b)] for a,b in zip(x,y)])

@log_call
def draw_mpl(T: float,
             zetas: List[float],
             wd_over_ws: List[float],
             wnT: List[float],
             theta_max: float,
             settling_sigma: Optional[float],
             pzs: List[PZ],
             style: Style,
             width: int,
             height: int,
             dpi: int,
             dark: bool,
             title: str,
             export_prefix: Optional[Path]) -> plt.Figure:

    if dark: plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=dpi)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-1.1, 1.1); ax.set_ylim(-1.1, 1.1)
    ax.set_xlabel("Re"); ax.set_ylabel("Im"); ax.set_title(title)

    th = np.linspace(0, 2*np.pi, 1200)
    ax.plot(np.cos(th), np.sin(th), "k-", lw=1, alpha=0.8, label="|z|=1")

    if settling_sigma is not None:
        rset = math.exp(-settling_sigma*T)
        circ = plt.Circle((0,0), rset, color=("0.85" if not dark else "0.2"),
                          alpha=0.35, label=f"|z|≤e^(-{settling_sigma:g}T)")
        ax.add_patch(circ)
        if export_prefix:
            xp, yp = ring_points(rset)
            _write_csv(export_prefix.with_name(export_prefix.name + "_settling.csv"),
                       ["radius","theta","x","y"],
                       [[rset, th, xp[i], yp[i]] for i, th in enumerate(np.linspace(0,2*np.pi,len(xp)))])

    for zeta in zetas:
        x, y = spiral_const_zeta(zeta, theta_max)
        ax.plot(x, y, color=style.zeta_color, lw=1.8, label=None)
        ax.plot(x, -y, color=style.zeta_color, lw=1.2, alpha=0.6, label=None)
        th_lab = min(0.7, theta_max*0.35)
        a = zeta/math.sqrt(1-zeta*zeta)
        rl = math.exp(-a*th_lab)
        ax.text(rl*math.cos(th_lab), rl*math.sin(th_lab), f"ζ={zeta:g}",
                color=style.zeta_color, fontsize=9)
        if export_prefix: _export_curve(export_prefix, f"zeta_{zeta:g}", x, y)

    for frac in wd_over_ws:
        theta = 2*math.pi*frac
        xr, yr = ray_theta(theta)
        ax.plot(xr, yr, color=style.ray_color, lw=1.0, label=None)
        ax.plot(xr, -yr, color=style.ray_color, lw=1.0, alpha=0.5, label=None)
        if frac not in (0.0, 0.5):
            ax.text(0.96*math.cos(theta), 0.96*math.sin(theta),
                    f"ωd/ωs={frac:g}", color=style.ray_color, fontsize=8,
                    ha="center", va="center")
        if export_prefix:
            _write_csv(export_prefix.with_name(export_prefix.name + "_rays.csv"),
                       ["wd_over_ws","theta","x_end","y_end"],
                       [[frac, theta, xr[-1], yr[-1]]], append=True)

    for val in wnT:
        x, y = curve_const_wnT(val)
        ax.plot(x, y, color=style.wn_color, lw=1.3, ls="--", label=None)
        ax.plot(x, -y, color=style.wn_color, lw=1.0, ls="--", alpha=0.6, label=None)
        idx = np.argmax(y)
        ax.text(x[idx], y[idx], f"ωnT={val:g}", color=style.wn_color, fontsize=8,
                ha="left", va="bottom")
        if export_prefix: _export_curve(export_prefix, f"wnT_{val:g}", x, y)

    if pzs:
        poles = [p for p in pzs if p.kind == "pole"]
        zeros = [z for z in pzs if z.kind == "zero"]
        if poles:
            ax.plot([p.z.real for p in poles], [p.z.imag for p in poles],
                    marker="x", ms=8, mew=2, ls="None", color=style.pole_color, label="poles")
        if zeros:
            ax.scatter([z.z.real for z in zeros], [z.z.imag for z in zeros],
                       s=50, facecolors=style.zero_face, edgecolors=style.zero_edge, label="zeros")
        for p in pzs:
            if p.label:
                ax.text(p.z.real, p.z.imag, f" {p.label}", fontsize=8)

    ax.grid(True, ls=":", alpha=0.45)
    return fig

def _legend_layout(loc: str) -> dict:
    if loc == "bottom":
        return dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5)
    if loc == "top":
        return dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0)
    if loc == "right":
        return dict(orientation="v", yanchor="top", y=1.0, xanchor="left", x=1.02)
    return dict(orientation="v", yanchor="bottom", y=0.02, xanchor="right", x=0.98, bgcolor="rgba(255,255,255,0.6)")

@log_call
def draw_plotly(T: float,
                zetas: List[float],
                wd_over_ws: List[float],
                wnT: List[float],
                theta_max: float,
                settling_sigma: Optional[float],
                pzs: List[PZ],
                title: str,
                width: int, height: int,
                legend_mode: str,
                legend_loc: str,
                responsive: bool,
                theme: str):
    if not _PLOTLY_OK:
        raise RuntimeError("Plotly is not installed. Try: pip install plotly")

    fig = go.Figure()
    th = np.linspace(0, 2*np.pi, 1200)
    fig.add_trace(go.Scatter(x=np.cos(th), y=np.sin(th),
                             mode="lines",
                             line=dict(color="black", width=1),
                             name="|z|=1"))
    if settling_sigma is not None:
        rset = math.exp(-settling_sigma*T)
        xs, ys = ring_points(rset)
        fig.add_trace(go.Scatter(x=xs, y=ys, fill="toself",
                                 fillcolor="rgba(128,128,128,0.25)",
                                 line=dict(color="rgba(128,128,128,0.35)", width=1),
                                 name=f"|z|≤e^(-{settling_sigma:g}T)"))

    first_z = True
    for zeta in zetas:
        x, y = spiral_const_zeta(zeta, theta_max)
        name = (f"ζ={zeta:g}" if legend_mode == "full" else ("constant ζ" if first_z else None))
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines",
                                 line=dict(color="#1f77b4", width=2),
                                 legendgroup="zeta", showlegend=(name is not None),
                                 name=name))
        fig.add_trace(go.Scatter(x=x, y=-y, mode="lines",
                                 line=dict(color="#1f77b4", width=1),
                                 legendgroup="zeta", showlegend=False))
        first_z = False

    first_ray = True
    for frac in wd_over_ws:
        theta = 2*math.pi*frac
        xr, yr = ray_theta(theta)
        name = (f"ωd/ωs={frac:g}" if legend_mode == "full" else ("ωd/ωs rays" if first_ray else None))
        fig.add_trace(go.Scatter(x=xr, y=yr, mode="lines",
                                 line=dict(color="#ff7f0e", width=1),
                                 legendgroup="rays", showlegend=(name is not None), name=name))
        fig.add_trace(go.Scatter(x=xr, y=-yr, mode="lines",
                                 line=dict(color="#ff7f0e", width=1),
                                 legendgroup="rays", showlegend=False))
        first_ray = False

    first_wn = True
    for val in wnT:
        x, y = curve_const_wnT(val)
        name = (f"ωnT={val:g}" if legend_mode == "full" else ("constant ωnT" if first_wn else None))
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines",
                                 line=dict(color="#2ca02c", width=1, dash="dash"),
                                 legendgroup="wn", showlegend=(name is not None), name=name))
        fig.add_trace(go.Scatter(x=x, y=-y, mode="lines",
                                 line=dict(color="#2ca02c", width=1, dash="dash"),
                                 legendgroup="wn", showlegend=False))
        first_wn = False

    poles_x, poles_y, zeros_x, zeros_y = [], [], [], []
    for p in pzs:
        if p.kind == "pole":
            poles_x.append(p.z.real); poles_y.append(p.z.imag)
        else:
            zeros_x.append(p.z.real); zeros_y.append(p.z.imag)
    if poles_x:
        fig.add_trace(go.Scatter(x=poles_x, y=poles_y, mode="markers",
                                 marker=dict(symbol="x", size=10, color="#d62728"),
                                 name="poles"))
    if zeros_x:
        fig.add_trace(go.Scatter(x=zeros_x, y=zeros_y, mode="markers",
                                 marker=dict(symbol="circle-open", size=10, color="#1f77b4"),
                                 name="zeros"))

    template = dict(plotly="plotly", plotly_white="plotly_white", plotly_dark="plotly_dark").get(theme, "plotly_white")
    fig.update_layout(
        template=template,
        title=dict(text=title, x=0.02, xanchor="left"),
        xaxis=dict(scaleanchor="y", scaleratio=1, zeroline=True, showgrid=True),
        yaxis=dict(zeroline=True, showgrid=True),
        legend=_legend_layout(legend_loc),
        legend_tracegroupgap=8,
        margin=dict(l=40, r=20, t=60, b=80 if legend_loc=="bottom" else 40)
    )
    if responsive:
        fig.update_layout(autosize=True)
    else:
        fig.update_layout(width=width, height=height)
    return fig
