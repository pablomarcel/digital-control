# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

import numpy as np

from .apis import Margins
from .utils import log_call

# ---------- frequency grid ----------

def make_nu_grid(T: float, nu_min: float = 1e-3, nu_max: float | None = None, pdec: int = 40) -> np.ndarray:
    if nu_max is None:
        nu_max = 2000.0 / max(T, 1e-6)
    N = max(200, int(np.log10(nu_max/nu_min) * pdec) + 1)
    return np.logspace(np.log10(nu_min), np.log10(nu_max), N)

# ---------- rational evaluation for polynomials ascending in w ----------

def eval_rational_asc(num_asc: Iterable[float], den_asc: Iterable[float], jw: np.ndarray) -> np.ndarray:
    num = np.zeros_like(jw, dtype=complex)
    den = np.zeros_like(jw, dtype=complex)
    pw  = np.ones_like(jw, dtype=complex)
    for c in list(num_asc):
        num += float(c) * pw
        pw *= jw
    pw  = np.ones_like(jw, dtype=complex)
    for c in list(den_asc):
        den += float(c) * pw
        pw *= jw
    return num/den

def bode_from_asc(num_asc: Iterable[float], den_asc: Iterable[float], nu: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    jw = 1j*nu
    H = eval_rational_asc(list(num_asc), list(den_asc), jw)
    mag_db    = 20*np.log10(np.maximum(np.abs(H), 1e-16))
    phase_deg = np.unwrap(np.angle(H))*180/np.pi
    return mag_db, phase_deg

# ---------- margins ----------

def _x_at_y(x: np.ndarray, y: np.ndarray, y0: float) -> float | None:
    s = np.sign(y - y0)
    idx = np.where(np.diff(s) != 0)[0]
    if len(idx) == 0: return None
    i = idx[0]
    x1,x2 = x[i], x[i+1]; y1,y2 = y[i], y[i+1]
    t = 0.0 if (y2==y1) else (y0 - y1)/(y2 - y1)
    return float(x1 + t*(x2 - x1))

def compute_margins(nu: np.ndarray, mag_db: np.ndarray, phase_deg: np.ndarray) -> Margins:
    nu_gc = _x_at_y(nu, mag_db, 0.0)
    nu_pc = _x_at_y(nu, phase_deg + 180.0, 0.0)
    pm = gm = None
    if nu_gc is not None:
        pm = 180.0 + float(np.interp(nu_gc, nu, phase_deg))
    if nu_pc is not None:
        gm = - float(np.interp(nu_pc, nu, mag_db))
    return Margins(nu_gc, nu_pc, pm, gm)

# ---------- plotting backends ----------

class MatplotlibPlotter:
    def __init__(self, save_pngs: bool = True):
        self.save_pngs = save_pngs

    def bode(self, nu, mag_db, phase_deg, title, out_png,
             corners: List[tuple[float,str]] | None = None,
             margins: Margins | None = None):
        import matplotlib.pyplot as plt
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.6, 7.6), sharex=True)
        ax1.semilogx(nu, mag_db, lw=2, label='|G(jν)| (dB)')
        ax1.axhline(0, color='k', ls='--', lw=0.9)
        ax1.grid(True, which='both', ls=':', lw=0.6)
        ax1.set_ylabel('Magnitude (dB)')

        ax2.semilogx(nu, phase_deg, lw=2, color='tab:red', label='∠G(jν) (deg)')
        ax2.axhline(-180, color='k', ls='--', lw=0.9)
        ax2.grid(True, which='both', ls=':', lw=0.6)
        ax2.set_xlabel(r'$\nu$ (rad/s)'); ax2.set_ylabel('Phase (deg)')

        if corners:
            for v,label in corners:
                ax1.axvline(v, color='0.5', ls=':', lw=1.0); ax2.axvline(v, color='0.5', ls=':', lw=1.0)
                ax1.text(v, ax1.get_ylim()[0]+3, label, rotation=90, ha='center', va='bottom', fontsize=8, color='0.4')

        if margins and margins.nu_gc:
            v = margins.nu_gc
            ax1.axvline(v, color='tab:green', ls='--'); ax2.axvline(v, color='tab:green', ls='--')
            ax2.plot([v],[float(np.interp(v, nu, phase_deg))],'o', color='tab:green',
                     label=f"PM≈{(margins.pm_deg or float('nan')):.1f}°")
            ax2.legend(loc='best')
        if margins and margins.nu_pc:
            v = margins.nu_pc
            ax1.axvline(v, color='tab:red', ls='--'); ax2.axvline(v, color='tab:red', ls='--')
            ax1.plot([v],[float(np.interp(v, nu, mag_db))],'o', color='tab:red',
                     label=f"GM≈{(margins.gm_db or float('nan')):.1f} dB")
            ax1.legend(loc='best')

        fig.suptitle(title)
        fig.tight_layout(rect=[0,0,1,0.96])
        fig.savefig(out_png, dpi=160)
        plt.close(fig)

class PlotlyPlotter:
    def bode(self, nu, mag_db, phase_deg, title, out_path, fmt,
             corners: List[tuple[float,str]] | None = None,
             margins: Margins | None = None):
        import plotly.graph_objs as go
        from plotly.subplots import make_subplots
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.06,
                            subplot_titles=(f"{title} — Magnitude", f"{title} — Phase"))
        fig.add_trace(go.Scatter(x=nu, y=mag_db, mode='lines', name='|G(jν)| (dB)',
                                 hovertemplate="ν=%{x:.5g} rad/s<br>|G|=%{y:.2f} dB"),
                      row=1, col=1)
        fig.add_hline(y=0, line=dict(color='black', width=1, dash='dash'), row=1, col=1)

        fig.add_trace(go.Scatter(x=nu, y=phase_deg, mode='lines', name='∠G(jν) (deg)',
                                 line=dict(color='firebrick'),
                                 hovertemplate="ν=%{x:.5g} rad/s<br>∠G=%{y:.1f}°"),
                      row=2, col=1)
        fig.add_hline(y=-180, line=dict(color='black', width=1, dash='dash'), row=2, col=1)

        if corners:
            for v,label in corners:
                fig.add_vline(x=v, line=dict(color='gray', dash='dot', width=1), row='all', col=1)
                fig.add_annotation(x=v, y=min(mag_db), text=label, showarrow=False,
                                   yshift=14, textangle=-90, font=dict(size=10, color='gray'),
                                   row=1, col=1)

        if margins and margins.nu_gc:
            v = margins.nu_gc; pm = float(margins.pm_deg) if margins.pm_deg is not None else float('nan')
            fig.add_vline(x=v, line=dict(color='green', dash='dash', width=2), row='all', col=1)
            fig.add_trace(go.Scatter(x=[v], y=[float(np.interp(v, nu, phase_deg))],
                                     mode='markers', marker=dict(color='green', size=9),
                                     name=f"PM≈{pm:.1f}°",
                                     hovertemplate=f"Gain crossover<br>ν_gc={v:.5g} rad/s<br>PM≈{pm:.1f}°"),
                          row=2, col=1)

        if margins and margins.nu_pc:
            v = margins.nu_pc; gm = float(margins.gm_db) if margins.gm_db is not None else float('nan')
            fig.add_vline(x=v, line=dict(color='red', dash='dash', width=2), row='all', col=1)
            fig.add_trace(go.Scatter(x=[v], y=[float(np.interp(v, nu, mag_db))],
                                     mode='markers', marker=dict(color='red', size=9),
                                     name=f"GM≈{gm:.1f} dB",
                                     hovertemplate=f"Phase crossover<br>ν_pc={v:.5g} rad/s<br>GM≈{gm:.1f} dB"),
                          row=1, col=1)

        fig.update_xaxes(type='log', title_text="ν (rad/s)", row=1, col=1)
        fig.update_xaxes(type='log', title_text="ν (rad/s)", row=2, col=1)
        fig.update_yaxes(title_text="Magnitude (dB)", row=1, col=1)
        fig.update_yaxes(title_text="Phase (deg)", row=2, col=1)
        fig.update_layout(title=title, autosize=True,
                          height=760,
                          legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1.0),
                          margin=dict(l=60, r=20, t=60, b=40))

        fmt = fmt.lower()
        if fmt == "html":
            html = fig.to_html(include_plotlyjs="cdn", full_html=True)
            html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>html,body,#wrap{{height:100%;margin:0}}#wrap{{display:flex;flex-direction:column}}#plot{{flex:1 1 auto;min-height:75vh}}</style>
</head><body><div id="wrap"><div id="plot">{html}</div></div></body></html>"""
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html)
        elif fmt in ("png", "svg", "pdf"):
            fig.write_image(out_path)  # requires kaleido
        else:
            raise ValueError("plotly-output must be: html | png | svg | pdf")
