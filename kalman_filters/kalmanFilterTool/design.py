from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import numpy as np
from .utils import out_path

@dataclass
class CSVExporter:
    out_dir: str = "kalman_filters/kalmanFilterTool/out"
    def write(self, t: np.ndarray, Y: np.ndarray, X_true: np.ndarray, X_hat: np.ndarray, filename: str = "kf.csv") -> str:
        p = Y.shape[0]; n = X_true.shape[0]
        cols = [t.reshape(-1,1)]; head = ["t"]
        for i in range(p):
            cols.append(Y[i,:].reshape(-1,1)); head.append(f"y{i+1}")
        for i in range(n):
            cols.append(X_true[i,:].reshape(-1,1)); head.append(f"x{i+1}_true")
        for i in range(n):
            cols.append(X_hat[i,:].reshape(-1,1)); head.append(f"x{i+1}_hat")
        M = np.hstack(cols)
        path = out_path(self.out_dir, filename, "kf.csv")
        import numpy as _np
        _np.savetxt(path, M, delimiter=",", header=",".join(head), comments="")
        return path

class Plotter:
    def __init__(self, backend: str = "both", out_dir: str = "kalman_filters/kalmanFilterTool/out", no_show: bool = False):
        self.backend = backend
        self.out_dir = out_dir
        self.no_show = no_show

    def mpl(self, t: np.ndarray, Y: np.ndarray, X_true: np.ndarray, X_hat: np.ndarray, save_png: Optional[str]):
        import matplotlib.pyplot as plt
        n = X_true.shape[0]; p = Y.shape[0]
        H = max(3.2, 1.6 * n)
        fig, ax = plt.subplots(1,1,figsize=(8.0,H))
        for i in range(n):
            ax.plot(t, X_true[i,:], label=f"x{i+1} true")
            ax.plot(t, X_hat[i,:],  label=f"x{i+1} hat")
        for i in range(p):
            ax.plot(t, Y[i,:], alpha=0.35, linestyle="--", label=f"y{i+1} meas")
        ax.grid(True, alpha=0.3)
        ax.set_title("Kalman filter (discrete-time)")
        ax.set_xlabel("t (s)"); ax.set_ylabel("value")
        ax.legend(ncol=2); fig.tight_layout()
        if save_png:
            png = out_path(self.out_dir, save_png, "kf.png")
            fig.savefig(png, dpi=150, bbox_inches="tight")
            print(f"Wrote {png}")
        if not self.no_show and self.backend == "mpl":
            plt.show()

    def plotly(self, t: np.ndarray, Y: np.ndarray, X_true: np.ndarray, X_hat: np.ndarray, save_html: Optional[str]):
        import plotly.graph_objects as go
        n = X_true.shape[0]; p = Y.shape[0]
        fig = go.Figure()
        for i in range(n):
            fig.add_trace(go.Scatter(x=t, y=X_true[i,:], mode="lines", name=f"x{i+1} true"))
            fig.add_trace(go.Scatter(x=t, y=X_hat[i,:],  mode="lines", name=f"x{i+1} hat"))
        for i in range(p):
            fig.add_trace(go.Scatter(x=t, y=Y[i,:], mode="lines", name=f"y{i+1} meas",
                                     opacity=0.35, line=dict(dash="dash")))
        fig.update_layout(title="Kalman filter (discrete-time)",
                          xaxis_title="t (s)", yaxis_title="value",
                          template="plotly_white",
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        html = out_path(self.out_dir, save_html, "kf.html")
        with open(html, "w", encoding="utf-8") as fh:
            fh.write(fig.to_html(full_html=True, include_plotlyjs="cdn", default_width="100%", default_height="70vh"))
        print(f"Wrote {html}")

    def render(self, t: np.ndarray, Y: np.ndarray, X_true: np.ndarray, X_hat: np.ndarray,
               save_png: Optional[str], save_html: Optional[str]):
        if self.backend in ("mpl","both"):
            self.mpl(t,Y,X_true,X_hat,save_png)
        if self.backend in ("plotly","both"):
            try:
                self.plotly(t,Y,X_true,X_hat,save_html)
            except Exception as e:
                raise SystemExit(f"[Fatal] Plotly requested but not available: {e}")
