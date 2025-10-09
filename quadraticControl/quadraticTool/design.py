from __future__ import annotations

import os
from typing import Dict

import numpy as np
from .utils import ensure_dir


def plot_series_mpl(
    series: Dict[str, np.ndarray],
    title: str,
    out_png: str,
    figsize: tuple[int, int] = (6, 4),
    dpi: int = 140,
    xlabel: str = "k",
    ylabel: str = "value",
) -> None:
    """
    Save a simple scatter-style plot (markers only) with matplotlib.

    Notes:
    - Uses a non-interactive backend for headless test environments.
    - Ensures the output directory exists.
    """
    # Use a headless backend (safe if already set; matplotlib ignores repeat calls after import)
    import matplotlib
    matplotlib.use("Agg")  # no-op if already configured

    import matplotlib.pyplot as plt

    plt.figure(figsize=figsize, dpi=dpi)
    for lab, y in series.items():
        y = np.asarray(y).squeeze()
        x = np.arange(len(y))
        plt.plot(x, y, linestyle="None", marker="o", markersize=3, label=lab)

    plt.grid(True, alpha=0.3)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()

    ensure_dir(os.path.dirname(out_png))
    plt.tight_layout()
    plt.savefig(out_png)
    plt.close()


def plot_series_plotly(
    series: Dict[str, np.ndarray],
    title: str,
    out_html: str,
    xlabel: str = "k",
    ylabel: str = "value",
) -> None:
    """
    Save a simple scatter plot page with Plotly.

    Ensures the output directory exists before writing.
    """
    try:
        import plotly.graph_objects as go
    except Exception as e:  # pragma: no cover - exercised only if plotly missing
        raise RuntimeError("plotly is required for plot_series_plotly") from e

    fig = go.Figure()
    for lab, y in series.items():
        y = np.asarray(y).squeeze()
        fig.add_trace(go.Scatter(y=y, mode="markers", name=lab, marker=dict(size=5)))

    fig.update_layout(title=title, xaxis_title=xlabel, yaxis_title=ylabel, template="plotly_white")
    ensure_dir(os.path.dirname(out_html))
    fig.write_html(out_html)
