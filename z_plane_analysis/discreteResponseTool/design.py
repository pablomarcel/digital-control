
from __future__ import annotations
import numpy as np
from typing import Optional, Dict, List
from .core import zroots_from_q, zpoly_from_q, roots_from_desc

try:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
except Exception:
    plt = None

try:
    import plotly.graph_objects as go
except Exception:
    go = None

def pretty_q(name: str, num, den) -> str:
    num = np.asarray(num); den = np.asarray(den)
    def term(c, k):
        if abs(c) < 1e-12: return None
        return f"{c:.6g}" if k==0 else f"{c:.6g}·q^{k}"
    def poly_to_str(v):
        parts = [t for k,c in enumerate(v) if (t:=term(c,k))]
        return (" + ".join(parts) if parts else "0").replace("q^1","q")
    return f"{name} = ({poly_to_str(num)}) / ({poly_to_str(den)})"

def unit_circle(ax, radius=1.0, **kw):
    if ax is None: return
    circ = Circle((0,0), radius, fill=False, ls='--', lw=1.2, ec='gray', alpha=0.6, **kw)
    ax.add_patch(circ)

def autoscale_square(ax, r: float):
    if ax is None: return
    ax.set_aspect('equal', 'box')
    ax.set_xlim([-r, r]); ax.set_ylim([-r, r])
    ax.axhline(0, color='k', lw=0.6, alpha=0.7)
    ax.axvline(0, color='k', lw=0.6, alpha=0.7)

def _track_branches(roots_seq: List[np.ndarray]) -> List[np.ndarray]:
    if not roots_seq: return []
    r0 = roots_seq[0]
    idx0 = np.argsort(np.angle(r0) + 1e-3*np.abs(r0))
    branches = [np.array([r0[i]]) for i in idx0]
    for t in range(1, len(roots_seq)):
        r_prev = np.array([b[-1] for b in branches])
        r_cur = roots_seq[t].copy()
        used = set()
        for j in range(len(branches)):
            d = np.abs(r_cur - r_prev[j])
            for u in used: d[u] = np.inf
            k = int(np.argmin(d)); used.add(k)
            branches[j] = np.append(branches[j], r_cur[k])
    return branches

def pzmap(numT_q, denT_q, path: Optional[str]=None, clip: float=2.0, title: str="Closed-loop T(z)"):
    if plt is None: return
    zzeros = zroots_from_q(numT_q); zpoles = zroots_from_q(denT_q)
    if (zzeros.size or zpoles.size):
        r = min(max(1.1, 1.1*np.max(np.abs(np.concatenate([zzeros, zpoles])))), clip if clip else 10.0)
    else:
        r = 1.1
    fig, ax = plt.subplots(figsize=(6,6))
    unit_circle(ax)
    ax.plot(np.real(zzeros), np.imag(zzeros), 'o', ms=9, label='zeros')
    ax.plot(np.real(zpoles), np.imag(zpoles), 'x', ms=11, mew=2, label='poles')
    autoscale_square(ax, r)
    ax.set_title(f"Pole–Zero Map: {title}")
    ax.set_xlabel("Re{z}"); ax.set_ylabel("Im{z}")
    ax.legend(loc='upper left')
    if path: fig.savefig(path, bbox_inches='tight', dpi=160)
    plt.close(fig)

def root_locus(numL_q, denL_q, Kmin: float=0.0, Kmax: float=20.0,
               NK: int=400, logscale: bool=False, rclip: float=2.5, path: Optional[str]=None,
               title: str="Root Locus of L(z)=K·Gd(z)G(z)"):
    if plt is None: return
    mD = len(denL_q) - 1
    mN = len(numL_q) - 1
    Dz = zpoly_from_q(denL_q, mD)
    Nz = zpoly_from_q(numL_q,  mN)
    L = max(len(Dz), len(Nz))
    DzL = np.pad(Dz, (0, L-len(Dz)))
    NzL = np.pad(Nz, (0, L-len(Nz)))

    if logscale:
        Kmin_pos = max(Kmin, 1e-6); K = np.logspace(np.log10(Kmin_pos), np.log10(Kmax), NK)
    else:
        K = np.linspace(Kmin, Kmax, NK)

    roots_seq = []
    for kappa in K:
        poly = DzL + kappa * NzL
        roots_seq.append(roots_from_desc(poly))

    branches = _track_branches(roots_seq)

    fig, ax = plt.subplots(figsize=(6,6))
    unit_circle(ax)
    for br in branches:
        br_clip = br[np.abs(br) <= (rclip if rclip else np.inf)]
        ax.plot(np.real(br_clip), np.imag(br_clip), lw=1.2, alpha=0.9, color='steelblue')
    z0 = roots_from_desc(NzL)
    p0 = roots_from_desc(DzL)
    ax.plot(np.real(z0), np.imag(z0), 'o', ms=9, label='zeros of L')
    ax.plot(np.real(p0), np.imag(p0), 'x', ms=11, mew=2, label='poles of L')

    autoscale_square(ax, rclip if rclip else 2.5)
    ax.set_title(f"{title}  (K ∈ [{Kmin:.0e}, {Kmax:.0e}] {'log' if logscale else 'lin'})")
    ax.set_xlabel("Re{z}"); ax.set_ylabel("Im{z}")
    ax.legend(loc='upper left')
    if path: fig.savefig(path, bbox_inches='tight', dpi=160)
    plt.close(fig)

def plotly_step(k, y, path, title="Response"):
    if go is None:
        print("[plotly] not available; install plotly"); return
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=k, y=y, mode='lines+markers', name='y[k]'))
    fig.update_layout(title=title, xaxis_title="k", yaxis_title="y[k]")
    fig.write_html(path)

def plotly_pz(numT_q, denT_q, path, clip=2.0):
    if go is None:
        print("[plotly] not available; install plotly"); return
    zzeros = zroots_from_q(numT_q); zpoles = zroots_from_q(denT_q)
    unit = np.exp(1j*np.linspace(0,2*np.pi,241))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=np.real(unit), y=np.imag(unit), mode='lines',
                             line=dict(dash='dash'), name='|z|=1'))
    fig.add_trace(go.Scatter(x=np.real(zzeros), y=np.imag(zzeros), mode='markers',
                             marker=dict(size=9), name='zeros'))
    fig.add_trace(go.Scatter(x=np.real(zpoles), y=np.imag(zpoles), mode='markers',
                             marker=dict(size=10, symbol='x'), name='poles'))
    fig.update_layout(title="PZ Map",
                      xaxis_title="Re{z}", yaxis_title="Im{z}",
                      xaxis=dict(scaleanchor="y", scaleratio=1, range=[-clip, clip]),
                      yaxis=dict(range=[-clip, clip]))
    fig.write_html(path)

def plotly_rlocus(numL_q, denL_q, path, Kmin=0.0, Kmax=20.0, NK=400, logscale=False, rclip=2.5):
    if go is None:
        print("[plotly] not available; install plotly"); return
    mD = len(denL_q) - 1
    mN = len(numL_q) - 1
    Dz = zpoly_from_q(denL_q, mD)
    Nz = zpoly_from_q(numL_q,  mN)
    Llen = max(len(Dz), len(Nz))
    DzL = np.pad(Dz, (0, Llen - len(Dz)))
    NzL = np.pad(Nz, (0, Llen - len(Nz)))

    if logscale:
        Kmin_pos = max(Kmin, 1e-6); K = np.logspace(np.log10(Kmin_pos), np.log10(Kmax), NK)
    else:
        K = np.linspace(Kmin, Kmax, NK)

    roots_seq = []
    for kappa in K:
        poly = DzL + kappa * NzL
        roots_seq.append(roots_from_desc(poly))

    branches = _track_branches(roots_seq)
    unit = np.exp(1j*np.linspace(0,2*np.pi,241))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=np.real(unit), y=np.imag(unit), mode='lines',
                             line=dict(dash='dash'), name='|z|=1'))
    for br in branches:
        br_clip = br[np.abs(br) <= rclip]
        fig.add_trace(go.Scatter(x=np.real(br_clip), y=np.imag(br_clip), mode='lines', showlegend=False))
    z0 = roots_from_desc(NzL); p0 = roots_from_desc(DzL)
    fig.add_trace(go.Scatter(x=np.real(z0), y=np.imag(z0), mode='markers', name='zeros of L'))
    fig.add_trace(go.Scatter(x=np.real(p0), y=np.imag(p0), mode='markers',
                             marker=dict(symbol='x', size=10), name='poles of L'))
    fig.update_layout(title=f"Root Locus  (K∈[{Kmin:.0e},{Kmax:.0e}] {'log' if logscale else 'lin'})",
                      xaxis_title="Re{z}", yaxis_title="Im{z}",
                      xaxis=dict(scaleanchor="y", scaleratio=1, range=[-rclip, rclip]),
                      yaxis=dict(range=[-rclip, rclip]))
    fig.write_html(path)

def panel_plot(step_k, step_y, numT_q, denT_q, numL_q, denL_q,
               path: Optional[str]=None, rclip: float=2.5, pzclip: float=2.0, metrics: Optional[Dict]=None):
    if plt is None: return
    fig = plt.figure(figsize=(13,4.8))
    gs = fig.add_gridspec(1,3, width_ratios=[1.2,1,1])
    ax0 = fig.add_subplot(gs[0,0])
    ax0.plot(step_k, step_y, '-o', ms=3)
    ax0.set_title("Response"); ax0.set_xlabel('k'); ax0.set_ylabel('y[k]')
    if metrics and metrics.get('k_settle') is not None:
        ax0.axvline(metrics['k_settle'], ls='--', c='g', alpha=0.6)
    ax1 = fig.add_subplot(gs[0,1])
    zzeros = zroots_from_q(numT_q); zpoles = zroots_from_q(denT_q)
    unit_circle(ax1); autoscale_square(ax1, pzclip)
    ax1.plot(np.real(zzeros), np.imag(zzeros), 'o', ms=7, label='zeros')
    ax1.plot(np.real(zpoles), np.imag(zpoles), 'x', ms=9, mew=2, label='poles')
    ax1.set_title("PZ map (T/H)"); ax1.legend(loc='upper left')
    ax2 = fig.add_subplot(gs[0,2])
    unit_circle(ax2); autoscale_square(ax2, rclip)
    mD = len(denL_q) - 1; mN = len(numL_q) - 1
    Dz = np.pad(zpoly_from_q(denL_q, mD), (0, max(0, mN-mD)))
    Nz = np.pad(zpoly_from_q(numL_q,  mN), (0, max(0, mD-mN)))
    z0 = roots_from_desc(Nz); p0 = roots_from_desc(Dz)
    ax2.plot(np.real(z0), np.imag(z0), 'o', ms=7, label='zeros of L')
    ax2.plot(np.real(p0), np.imag(p0), 'x', ms=9, mew=2, label='poles of L')
    ax2.set_title("Root locus (windowed)"); ax2.legend(loc='upper left')
    if path: fig.savefig(path, bbox_inches='tight', dpi=160)
    plt.close(fig)
