from __future__ import annotations
from typing import Dict, List, Optional
import math

from .io import unit_scale_map
from .utils import timed

# Matplotlib plotting
import matplotlib
matplotlib.use('Agg')  # headless-safe
import matplotlib.pyplot as plt

# Plotly plotting (optional)
try:
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go
    _HAS_PLOTLY = True
except Exception:
    _HAS_PLOTLY = False

@timed
def plot_mpl(png_path: Optional[str], times_sec: List[float], series: Dict[str, List[float]], widths: Dict[str,int], xunits: str, title: str) -> None:
    n = len(series)
    fig, axes = plt.subplots(n, 1, figsize=(10, 1.9*n), sharex=True)
    if n == 1: axes = [axes]
    names = list(series.keys())
    xscale = unit_scale_map()[xunits]
    tx = [t * xscale for t in times_sec]
    for ax, name in zip(axes, names):
        vals = series[name]
        ax.step(tx, vals, where='post'); ax.set_ylabel(name)
        if widths[name] == 1:
            try:
                finite = [v for v in vals if not (isinstance(v, float) and math.isnan(v))]
                if set(finite) <= {0,1}: ax.set_ylim(-0.2, 1.2)
            except Exception: pass
        ax.grid(True, alpha=0.3)
    axes[-1].set_xlabel(f"time [{xunits}]")
    fig.suptitle(title); fig.tight_layout(rect=[0,0,1,0.95])
    if png_path:
        fig.savefig(png_path, dpi=160); print(f"Wrote PNG to {png_path}")
    plt.close(fig)

@timed
def plot_plotly(html_path: Optional[str], times_sec: List[float], series: Dict[str, List[float]], widths: Dict[str,int], xunits: str, title: str, overlay=False) -> None:
    if not _HAS_PLOTLY:
        raise RuntimeError("Plotly not installed. Try: pip install plotly")
    names = list(series.keys())
    xscale = unit_scale_map()[xunits]
    tx = [t * xscale for t in times_sec]
    if overlay:
        fig = make_subplots(rows=1, cols=1, shared_xaxes=True)
        for name in names:
            fig.add_trace(go.Scatter(x=tx, y=series[name], name=name, mode='lines', line=dict(shape='hv')), row=1, col=1)
        fig.update_yaxes(title_text="value", row=1, col=1); height = 500
    else:
        rows = len(names)
        vspace = 0.06 if rows <= 1 else min(0.04, 0.8 / (rows - 1))
        if rows >= 20:
            print(f"[hint] You are plotting {rows} rows. Consider overlay or fewer signals for readability.")
        fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, subplot_titles=names, vertical_spacing=vspace)
        for r, name in enumerate(names, start=1):
            fig.add_trace(go.Scatter(x=tx, y=series[name], name=name, mode='lines', line=dict(shape='hv')), row=r, col=1)
            if widths[name] == 1: fig.update_yaxes(range=[-0.2, 1.2], row=r, col=1)
            fig.update_yaxes(title_text=name, row=r, col=1)
        height = min(max(300, rows * 140), 3000)
    fig.update_layout(title=title, xaxis_title=f"time [{xunits}]", template="plotly_white", showlegend=overlay, height=height, margin=dict(t=60,b=40,l=60,r=20))
    if html_path:
        fig.write_html(html_path, include_plotlyjs='cdn'); print(f"Wrote HTML to {html_path}")
