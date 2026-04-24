
from __future__ import annotations

from typing import List

import numpy as np

from .core import (
    design_prediction_observer, design_current_observer, dlqe_gain,
    design_minimum_order_observer, k0_state, k0_ogata,
    ke_rule_of_thumb, ke_grid_search, simulate_full_observer
)
from .io import parse_matrix, parse_poles
from .utils import eigvals_sorted, multiset_close, save_json, save_csv_matrix, save_csv_series, out_path


def design_observer(kind: str, A, C, poles=None, B=None, method="place",
                    G=None, Qn=None, Rn=None, csv=None, out=None):
    A = parse_matrix(A); C = parse_matrix(C)
    if kind == "prediction":
        L = design_prediction_observer(A, C, parse_poles(poles), method)
        payload = {"L": L, "eig(A-LC)": eigvals_sorted(A - L @ C)}
        if csv: save_csv_matrix(out_path(csv), L, header=["L"])
        if out: save_json(out_path(out), payload)
        return payload
    elif kind == "current":
        Lc = design_current_observer(A, C, parse_poles(poles), method)
        payload = {"Lc": Lc, "eig(A-LcCA)": eigvals_sorted(A - Lc @ C @ A)}
        if csv: save_csv_matrix(out_path(csv), Lc, header=["Lc"])
        if out: save_json(out_path(out), payload)
        return payload
    elif kind == "dlqe":
        L, P, E = dlqe_gain(A, parse_matrix(G), C, parse_matrix(Qn), parse_matrix(Rn))
        payload = {"L": L, "P": P, "eig(A-LC)": eigvals_sorted(A - L @ C)}
        if csv: save_csv_matrix(out_path(csv), L, header=["L"])
        if out: save_json(out_path(out), payload)
        return payload
    elif kind == "min":
        d = design_minimum_order_observer(A, parse_matrix(B), C, parse_poles(poles), method)
        payload = {"Ke": d.Ke, "err_poles": list(d.err_poles), "T": d.T, "notes": "Ke, T are in measured-form coords"}
        if csv: save_csv_matrix(out_path(csv), d.Ke, header=["Ke"])
        if out: save_json(out_path(out), payload)
        return payload
    else:
        raise ValueError(f"Unknown kind: {kind}")


def closedloop_poles(A, B, C, K, L, out=None):
    A = parse_matrix(A); B = parse_matrix(B); C = parse_matrix(C); K = parse_matrix(K); L = parse_matrix(L)
    union = eigvals_sorted(A - B @ K) + eigvals_sorted(A - L @ C)
    Acl = np.block([[A - B @ K,           B @ K],
                    [np.zeros_like(A),    A - L @ C]])
    vals = eigvals_sorted(Acl)
    payload = {"eig_union": union, "eig_augmented": vals, "separation_ok": multiset_close(union, vals, tol=1e-7)}
    if out: save_json(out_path(out), payload)
    return payload


def compute_k0(A, B, C, K, L=None, mode="state", ogata_extra_gain=None, out=None):
    A = parse_matrix(A); B = parse_matrix(B); C = parse_matrix(C); K = parse_matrix(K)
    if mode == "ogata":
        if L is None:
            raise ValueError("Ogata K0 mode requires L.")
        Lm = parse_matrix(L)
        k0 = k0_ogata(A, B, C, K, Lm, extra_gain=ogata_extra_gain)
    else:
        k0 = k0_state(A, B, C, K)
    payload = {"K0": k0, "mode": mode}
    if out: save_json(out_path(out), payload)
    return payload


def select_L(A, B, C, K, method="place", rule_of_thumb=None, speedup=5.0, sweep=None, steps=200, dlqe=False, G=None, Qn=None, Rn=None, csv=None, out=None):
    A = parse_matrix(A); B = parse_matrix(B); C = parse_matrix(C); K = parse_matrix(K)
    if rule_of_thumb:
        poles = parse_poles(rule_of_thumb)
        L, poles = ke_rule_of_thumb(A, C, poles, speedup=speedup, method=method)
        payload = {"L": L, "poles": poles}
    elif sweep:
        combos = [[complex(z.replace("i","j")) for z in c.replace(" ", "").split(",")] for c in sweep.split(";") if c.strip()]
        score, poles, L = ke_grid_search(A, C, B, K, combos, steps=steps)
        payload = {"best_score": score, "poles": poles, "L": L}
    elif dlqe:
        L, P, E = dlqe_gain(A, parse_matrix(G), C, parse_matrix(Qn), parse_matrix(Rn))
        payload = {"L": L, "eig(A-LC)": eigvals_sorted(A - L @ C)}
    else:
        raise ValueError("No selection mode specified.")
    if payload.get("L") is not None and csv:
        save_csv_matrix(out_path(csv), payload["L"], header=["L"])
    if out: save_json(out_path(out), payload)
    return payload


def simulate(A, B, C, K, L, N=60, Ts=1.0, ref="step", K0=None, k0_mode="state", ogata_extra_gain=None, csv=None, out=None,
             plot=False, plot_type="points", plotly=False, html=None):
    A = parse_matrix(A); B = parse_matrix(B); C = parse_matrix(C); K = parse_matrix(K); L = parse_matrix(L)
    if ref == "step":
        r = np.ones((N, 1))
    elif ref == "ramp":
        r = Ts * np.arange(N).reshape(N, 1)
    else:
        r = np.zeros((N, 1))

    if K0 == "auto":
        if k0_mode == "ogata":
            K0v = k0_ogata(A, B, C, K, L, extra_gain=ogata_extra_gain)
        else:
            K0v = k0_state(A, B, C, K)
    elif K0 is None:
        K0v = None
    else:
        K0v = float(K0)

    res = simulate_full_observer(A, B, C, K, L, N=N, r=r, Ts=Ts, K0=K0v)
    y = np.squeeze(np.array(res["y"], float)).tolist()
    u = np.squeeze(np.array(res["u"], float)).tolist()
    t = res["t"].tolist()
    payload = {"K0": K0v, "k0_mode": k0_mode, "y": y, "u": u}
    if csv:
        save_csv_series(out_path(csv), {"t": t, "y": y, "u": u})
    if out:
        save_json(out_path(out), payload)

    # plotting on demand (no heavy deps for tests)
    if plot:
        import matplotlib.pyplot as plt
        plt.figure()
        if plot_type == "stairs":
            plt.step(t, y, where="post")
        elif plot_type == "line":
            plt.plot(t, y)
        else:
            plt.plot(t, y, "o", markersize=4)
        plt.title("y(k)")
        plt.grid(True)

        plt.figure()
        if plot_type == "stairs":
            plt.step(t, u, where="post")
        elif plot_type == "line":
            plt.plot(t, u)
        else:
            plt.plot(t, u, "o", markersize=4)
        plt.title("u(k)")
        plt.grid(True)
        plt.show()

    if plotly:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=("Output y(k)","Control u(k)"))
        if plot_type == "stairs":
            fig.add_trace(go.Scatter(x=t, y=y, mode="lines", line_shape="hv", name="y"), row=1, col=1)
            fig.add_trace(go.Scatter(x=t, y=u, mode="lines", line_shape="hv", name="u"), row=2, col=1)
        elif plot_type == "line":
            fig.add_trace(go.Scatter(x=t, y=y, mode="lines", name="y"), row=1, col=1)
            fig.add_trace(go.Scatter(x=t, y=u, mode="lines", name="u"), row=2, col=1)
        else:
            fig.add_trace(go.Scatter(x=t, y=y, mode="markers", name="y"), row=1, col=1)
            fig.add_trace(go.Scatter(x=t, y=u, mode="markers", name="u"), row=2, col=1)
        fig.update_layout(height=700, width=900, title="Observer Simulation")
        if html:
            p = out_path(html)
            p.write_text(fig.to_html(include_plotlyjs="cdn"))
        fig.show()

    return payload
