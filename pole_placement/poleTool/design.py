from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
import numpy as np
from .utils import ensure_out_dir, mat_to_str, to_real_if_close
from .io import safeify

def save_json(summary: Dict[str, Any], outdir: Path, name: str) -> Path:
    out = outdir / f"{name}.json"
    import json
    with open(out, "w", encoding="utf-8") as f:
        json.dump(safeify(summary), f, indent=2)
    return out

def save_csv_step(k, y, outdir: Path, name: str) -> Path:
    out = outdir / f"{name}_step.csv"
    k = np.asarray(k).ravel()
    y = np.asarray(y)
    m = y.shape[0] if y.ndim == 2 else 1
    with open(out, "w", encoding="utf-8") as f:
        if m == 1:
            f.write("k,y\n")
            yy = y[0, :] if y.ndim == 2 else y
            for i, ki in enumerate(k):
                f.write(f"{int(ki)},{float(np.real(yy[i]))}\n")
        else:
            f.write("k," + ",".join([f"y{j+1}" for j in range(m)]) + "\n")
            for i, ki in enumerate(k):
                vals = [float(np.real(y[j, i])) for j in range(m)]
                f.write(f"{int(ki)}," + ",".join(str(v) for v in vals) + "\n")
    return out

def _lazy_import_mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt

def _lazy_import_plotly():
    import plotly.graph_objects as go
    from plotly.offline import plot as plotly_offline
    return go, plotly_offline

def plot_step(k, y, backend: str, style: str, outfile: Path):
    if backend == "mpl":
        plt = _lazy_import_mpl()
        plt.figure(figsize=(8, 6), dpi=150)
        if y.ndim == 1:
            yy = np.real(y).ravel()
            if style == "dots":
                plt.plot(k, yy, "o", markersize=4)
            elif style == "stairs":
                plt.step(k, yy, where="post")
            else:
                plt.plot(k, yy)
        else:
            for j in range(y.shape[0]):
                yy = np.real(y[j, :]).ravel()
                if style == "dots":
                    plt.plot(k, yy, "o", markersize=4, label=f"y{j+1}")
                elif style == "stairs":
                    plt.step(k, yy, where="post", label=f"y{j+1}")
                else:
                    plt.plot(k, yy, label=f"y{j+1}")
            plt.legend()
        plt.title("Unit-step response")
        plt.xlabel("k (samples)")
        plt.ylabel("y(k)")
        plt.grid(True, ls=":", alpha=0.6)
        plt.tight_layout()
        plt.savefig(outfile)
        plt.close()
    elif backend == "plotly":
        go, plotly_offline = _lazy_import_plotly()
        fig = go.Figure()
        mode = "markers" if style == "dots" else ("lines" if style == "connected" else "lines")
        if y.ndim == 1:
            fig.add_trace(go.Scatter(x=k, y=np.real(y).ravel(), mode=mode, name="y"))
        else:
            for j in range(y.shape[0]):
                fig.add_trace(go.Scatter(x=k, y=np.real(y[j, :]).ravel(), mode=mode, name=f"y{j+1}"))
        fig.update_layout(title="Unit-step response", xaxis_title="k (samples)", yaxis_title="y(k)")
        plotly_offline(fig, filename=str(outfile), auto_open=False)
