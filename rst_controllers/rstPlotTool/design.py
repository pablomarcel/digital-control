from __future__ import annotations
import os
from typing import Dict, List, Optional, Tuple
import numpy as np

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    _HAS_PLOTLY = True
except Exception:
    _HAS_PLOTLY = False

import matplotlib
import matplotlib.pyplot as plt

from .core import robust_limits
from .utils import with_out_dir

def apply_mpl_style(style: str, dpi: int) -> None:
    style = style.lower()
    if style == "dark":
        plt.style.use("dark_background")
        matplotlib.rcParams.update({
            "figure.dpi": dpi, "savefig.dpi": dpi,
            "axes.grid": True, "grid.alpha": 0.25,
            "axes.titlesize": 14, "axes.labelsize": 11,
            "legend.fontsize": 9, "lines.linewidth": 2.0,
        })
    elif style == "light":
        plt.style.use("seaborn-v0_8-whitegrid")
        matplotlib.rcParams.update({
            "figure.dpi": dpi, "savefig.dpi": dpi,
            "axes.titlesize": 14, "axes.labelsize": 11,
            "legend.fontsize": 9, "lines.linewidth": 2.0,
        })
    else:
        plt.style.use("classic")
        matplotlib.rcParams.update({
            "figure.dpi": dpi, "savefig.dpi": dpi,
            "axes.grid": True, "grid.linestyle": "-", "grid.alpha": 0.35,
            "axes.titlesize": 14, "axes.labelsize": 11,
            "legend.fontsize": 9, "lines.linewidth": 1.6,
        })

def plotly_template_for(style: str) -> str:
    return "plotly_dark" if style.lower() == "dark" else "plotly_white"

def make_plotly_figure(template: str):
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        vertical_spacing=0.075,
                        subplot_titles=("r & y", "u", "e"))
    fig.update_layout(template=template)
    fig.update_xaxes(title_text="k (samples)", row=3, col=1)
    fig.update_yaxes(title_text="r, y", row=1, col=1)
    fig.update_yaxes(title_text="u", row=2, col=1)
    fig.update_yaxes(title_text="e", row=3, col=1)
    return fig

@with_out_dir
def mpl_single(figpath: str,
               data: Dict[str, np.ndarray],
               title: str,
               style: str,
               dpi: int,
               ylims: Tuple[Optional[Tuple[float,float]], Optional[Tuple[float,float]], Optional[Tuple[float,float]]] = (None,None,None),
               annotate: Optional[dict] = None) -> None:
    apply_mpl_style(style, dpi)
    k, r, y, u, e = data["k"], data["r"], data["y"], data["u"], data["e"]
    fig, axes = plt.subplots(3, 1, figsize=(12, 7), sharex=True)
    ax1, ax2, ax3 = axes
    ax1.plot(k, r, label="r (reference)")
    ax1.plot(k, y, label="y (output)")
    ax1.set_ylabel("r, y"); ax1.legend(loc="lower right")
    ax2.plot(k, u, label="u (control)")
    ax2.set_ylabel("u"); ax2.legend(loc="upper right")
    ax3.plot(k, e, label="e = r - y")
    ax3.set_ylabel("e"); ax3.set_xlabel("k (samples)"); ax3.legend(loc="upper right")

    if ylims[0]: ax1.set_ylim(*ylims[0])
    if ylims[1]: ax2.set_ylim(*ylims[1])
    if ylims[2]: ax3.set_ylim(*ylims[2])

    fig.suptitle(title)

    if annotate:
        try:
            A = annotate["plant"]["A"]
            B = annotate["plant"]["B"]
            d = annotate["plant"]["d"]
            Acl = annotate["target"]["Acl"]
            R = annotate["controller"]["R"]
            S = annotate["controller"]["S"]
            T = annotate["controller"]["T"]
            txt = (f"A(q) = {A}\\nB(q) = {B}\\nd = {d}\\n"
                   f"A_cl(q) = {Acl}\\nR(q) = {R}\\nS(q) = {S}\\nT(q) = {T}")
            ax1.text(0.01, 0.98, txt, ha="left", va="top",
                     transform=ax1.transAxes,
                     bbox=dict(boxstyle="round", facecolor="white", alpha=0.75, lw=0.5),
                     fontsize=9)
        except Exception:
            pass

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(figpath, bbox_inches="tight")
    plt.close(fig)

@with_out_dir
def mpl_overlay(figpath: str,
                files: List[str],
                datasets: List[Dict[str, np.ndarray]],
                style: str,
                dpi: int,
                legend_mode: str = "compact",
                robust: float = 0.995,
                ylims: Tuple[Optional[Tuple[float,float]], Optional[Tuple[float,float]], Optional[Tuple[float,float]]] = (None,None,None),
                clip_to_limits: bool = False,
                title: str = "RST Step — Overlay") -> None:
    apply_mpl_style(style, dpi)

    fig, axes = plt.subplots(3, 1, figsize=(14, 7.5), sharex=True)
    ax1, ax2, ax3 = axes

    if not any(ylims):
        y_all = np.concatenate([d["y"] for d in datasets if len(d["y"])])
        u_all = np.concatenate([d["u"] for d in datasets if len(d["u"])])
        e_all = np.concatenate([d["e"] for d in datasets if len(d["e"])])
        ylimY = robust_limits(y_all, robust)
        ylimU = robust_limits(u_all, robust)
        ylimE = robust_limits(e_all, robust)
    else:
        ylimY, ylimU, ylimE = ylims

    for name, d in zip([os.path.basename(p) for p in files], datasets):
        k, r, y, u, e = d["k"], d["r"], d["y"], d["u"], d["e"]
        if clip_to_limits:
            if ylimY: y = np.clip(y, *ylimY); r = np.clip(r, *ylimY)
            if ylimU: u = np.clip(u, *ylimU)
            if ylimE: e = np.clip(e, *ylimE)
        ax1.plot(k, r, ls="--", lw=1.0, alpha=0.9, label=f"r ({name})" if legend_mode=="full" else None)
        ax1.plot(k, y, lw=1.8, alpha=0.95, label=f"y ({name})")
        ax2.plot(k, u, lw=1.6, alpha=0.95, label=f"u ({name})" if legend_mode=="full" else None)
        ax3.plot(k, e, lw=1.3, alpha=0.95, label=f"e ({name})" if legend_mode=="full" else None)

    ax1.set_ylabel("r, y")
    ax2.set_ylabel("u")
    ax3.set_ylabel("e"); ax3.set_xlabel("k (samples)")

    if ylimY: ax1.set_ylim(*ylimY)
    if ylimU: ax2.set_ylim(*ylimU)
    if ylimE: ax3.set_ylim(*ylimE)

    if legend_mode == "full":
        ax1.legend(loc="upper right", ncol=1, fontsize=8)
        ax2.legend(loc="upper right", ncol=1, fontsize=8)
        ax3.legend(loc="upper right", ncol=1, fontsize=8)
    elif legend_mode == "compact":
        ax1.legend(loc="upper right", ncol=1, fontsize=8)

    fig.suptitle(title)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(figpath, bbox_inches="tight")
    plt.close(fig)

@with_out_dir
def plotly_single(htmlpath: str,
                  data: Dict[str, np.ndarray],
                  title: str,
                  style: str,
                  ylims: Tuple[Optional[Tuple[float,float]], Optional[Tuple[float,float]], Optional[Tuple[float,float]]] = (None,None,None),
                  annotate: Optional[dict] = None) -> None:
    if not _HAS_PLOTLY:
        return
    template = plotly_template_for(style)
    k, r, y, u, e = data["k"], data["r"], data["y"], data["u"], data["e"]
    fig = make_plotly_figure(template)
    fig.add_trace(go.Scatter(x=k, y=r, name="r (reference)"), row=1, col=1)
    fig.add_trace(go.Scatter(x=k, y=y, name="y (output)"), row=1, col=1)
    fig.add_trace(go.Scatter(x=k, y=u, name="u (control)"), row=2, col=1)
    fig.add_trace(go.Scatter(x=k, y=e, name="e = r - y"), row=3, col=1)

    if ylims[0]: fig.update_yaxes(range=list(ylims[0]), row=1, col=1)
    if ylims[1]: fig.update_yaxes(range=list(ylims[1]), row=2, col=1)
    if ylims[2]: fig.update_yaxes(range=list(ylims[2]), row=3, col=1)

    if annotate:
        try:
            A = annotate["plant"]["A"]; B = annotate["plant"]["B"]; d = annotate["plant"]["d"]
            Acl = annotate["target"]["Acl"]
            R = annotate["controller"]["R"]; S = annotate["controller"]["S"]; T = annotate["controller"]["T"]
            txt = (f"A={A}<br>B={B}<br>d={d}<br>"
                   f"A_cl={Acl}<br>R={R}<br>S={S}<br>T={T}")
            fig.add_annotation(text=txt, xref="paper", yref="paper",
                               x=0.01, y=0.99, xanchor="left", yanchor="top",
                               bgcolor="rgba(255,255,255,0.75)", bordercolor="rgba(0,0,0,0.25)",
                               showarrow=False, font=dict(size=12))
        except Exception:
            pass

    fig.update_layout(title=title, height=780, width=1440, template=template)
    fig.write_html(htmlpath)

@with_out_dir
def plotly_overlay(htmlpath: str,
                   files: List[str],
                   datasets: List[Dict[str, np.ndarray]],
                   style: str,
                   legend_mode: str = "compact",
                   robust: float = 0.995,
                   ylims: Tuple[Optional[Tuple[float,float]], Optional[Tuple[float,float]], Optional[Tuple[float,float]]] = (None,None,None),
                   title: str = "RST Step — Overlay") -> None:
    if not _HAS_PLOTLY:
        return
    template = plotly_template_for(style)
    fig = make_plotly_figure(template)

    if not any(ylims):
        y_all = np.concatenate([d["y"] for d in datasets if len(d["y"])])
        u_all = np.concatenate([d["u"] for d in datasets if len(d["u"])])
        e_all = np.concatenate([d["e"] for d in datasets if len(d["e"])])
        ylimY = robust_limits(y_all, robust)
        ylimU = robust_limits(u_all, robust)
        ylimE = robust_limits(e_all, robust)
    else:
        ylimY, ylimU, ylimE = ylims

    for name, d in zip([os.path.basename(p) for p in files], datasets):
        k, r, y, u, e = d["k"], d["r"], d["y"], d["u"], d["e"]
        fig.add_trace(go.Scatter(x=k, y=y, name=f"y ({name})"), row=1, col=1)
        if legend_mode == "full":
            fig.add_trace(go.Scatter(x=k, y=r, name=f"r ({name})", line=dict(dash="dash")), row=1, col=1)
            fig.add_trace(go.Scatter(x=k, y=u, name=f"u ({name})"), row=2, col=1)
            fig.add_trace(go.Scatter(x=k, y=e, name=f"e ({name})"), row=3, col=1)

    if ylimY: fig.update_yaxes(range=list(ylimY), row=1, col=1)
    if ylimU: fig.update_yaxes(range=list(ylimU), row=2, col=1)
    if ylimE: fig.update_yaxes(range=list(ylimE), row=3, col=1)

    fig.update_layout(title=title, height=780, width=1440, template=template,
                      legend=dict(orientation="v"))
    fig.write_html(htmlpath)
