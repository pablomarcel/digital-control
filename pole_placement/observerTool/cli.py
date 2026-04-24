
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import os
import sys

# ---------- Import shim so `python cli.py` works with absolute imports ----------
if __package__ in (None, ""):
    # Running as a script: add project root to sys.path and import absolute modules
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)

    from pole_placement.observerTool.apis import (
        DesignRequest, ClosedLoopRequest, K0Request, SelectRequest, SimRequest, ExampleRequest
    )
    from pole_placement.observerTool.app import ObserverApp
else:
    # Normal package execution
    from .apis import (
        DesignRequest, ClosedLoopRequest, K0Request, SelectRequest, SimRequest, ExampleRequest
    )
    from .app import ObserverApp


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pole_placement.observerTool",
                                description="Observer design tool (prediction/current/min, DLQE, closed-loop, K0, selection, sim)")
    sub = p.add_subparsers(dest="cmd", required=True)

    # design
    d = sub.add_parser("design", help="Design observer gains (prediction/current/dlqe/min)")
    d.add_argument("--type", choices=["prediction","current","dlqe","min"], required=True)
    d.add_argument("--A"); d.add_argument("--C")
    d.add_argument("--method", choices=["place","acker"], default="place")
    d.add_argument("--poles", help="Comma-separated poles for prediction/current/min")
    d.add_argument("--B", help="Required for minimum-order")
    d.add_argument("--G", help="Process-noise input matrix for dlqe")
    d.add_argument("--Qn", help="Process-noise covariance for dlqe")
    d.add_argument("--Rn", help="Measurement-noise covariance for dlqe")
    d.add_argument("--csv", help="Export CSV to out/…")
    d.add_argument("--out", help="Export JSON to out/…")

    # closed loop
    cl = sub.add_parser("closedloop", help="Closed-loop poles and separation principle check")
    cl.add_argument("--A"); cl.add_argument("--B"); cl.add_argument("--C")
    cl.add_argument("--K"); cl.add_argument("--L")
    cl.add_argument("--out", help="Export JSON to out/…")

    # k0
    k0 = sub.add_parser("k0", help="Compute SISO prefilter K0 (state/ogata)")
    k0.add_argument("--A"); k0.add_argument("--B"); k0.add_argument("--C"); k0.add_argument("--K")
    k0.add_argument("--L", help="Needed for ogata mode")
    k0.add_argument("--mode", choices=["state","ogata"], default="state")
    k0.add_argument("--ogata-extra-gain", type=float, default=None)
    k0.add_argument("--out", help="Export JSON to out/…")

    # select
    sel = sub.add_parser("select", help="Select L via rule-of-thumb, DLQE, or grid sweep")
    sel.add_argument("--A"); sel.add_argument("--B"); sel.add_argument("--C"); sel.add_argument("--K")
    sel.add_argument("--method", choices=["place","acker"], default="place")
    sel.add_argument("--rule-of-thumb", help="Comma poles of plant (e.g., '0.6+0.4j,0.6-0.4j')")
    sel.add_argument("--speedup", type=float, default=5.0)
    sel.add_argument("--sweep", help="Pole sets separated by ';', each comma-separated, e.g. '0.2,0.2; 0.4+0.4j,0.4-0.4j'")
    sel.add_argument("--steps", type=int, default=200)
    sel.add_argument("--dlqe", action="store_true")
    sel.add_argument("--G"); sel.add_argument("--Qn"); sel.add_argument("--Rn")
    sel.add_argument("--csv", help="Export CSV of best L to out/…")
    sel.add_argument("--out", help="Export JSON summary to out/…")

    # sim
    sim = sub.add_parser("sim", help="Simulate plant+observer+state-feedback; step/ramp and auto K0")
    sim.add_argument("--A"); sim.add_argument("--B"); sim.add_argument("--C")
    sim.add_argument("--K"); sim.add_argument("--L")
    sim.add_argument("--N", type=int, default=60); sim.add_argument("--Ts", type=float, default=1.0)
    sim.add_argument("--ref", choices=["none","step","ramp"], default="step")
    sim.add_argument("--K0", help="'auto' or numeric", default=None)
    sim.add_argument("--k0-mode", choices=["state","ogata"], default="state")
    sim.add_argument("--ogata-extra-gain", type=float, default=None)
    sim.add_argument("--csv", help="Export CSV (t,y,u) to out/…")
    sim.add_argument("--out", help="Export JSON to out/…")
    sim.add_argument("--plot", action="store_true", help="Show Matplotlib plots")
    sim.add_argument("--plot-type", choices=["points","stairs","line"], default="points")
    sim.add_argument("--plotly", action="store_true", help="Show Plotly figure")
    sim.add_argument("--html", help="Save Plotly HTML to out/...")

    # examples
    ex = sub.add_parser("example", help="Run textbook examples (6-9, 6-10, 6-11, 6-12)")
    ex.add_argument("--which", choices=["6-9","6-10","6-11","6-12"], required=True)
    ex.add_argument("--Ts", type=float, default=0.2)

    return p


def main():
    parser = build_parser()
    ns = parser.parse_args()
    app = ObserverApp()

    if ns.cmd == "design":
        if ns.type in ("prediction","current","min") and not ns.poles:
            parser.error("--poles required for 'prediction', 'current', and 'min'.")
        if ns.type == "min" and not ns.B:
            parser.error("--B is required for minimum-order.")
        if ns.type == "dlqe" and not (ns.G and ns.Qn and ns.Rn):
            parser.error("--G, --Qn, --Rn are required for dlqe.")
        req = DesignRequest(kind=ns.type, A=ns.A, C=ns.C, poles=ns.poles, B=ns.B, method=ns.method,
                            G=ns.G, Qn=ns.Qn, Rn=ns.Rn, csv=ns.csv, out=ns.out)
        out = app.run(req)

    elif ns.cmd == "closedloop":
        for k in ("A","B","C","K","L"):
            if getattr(ns, k) is None:
                parser.error(f"--{k} is required")
        req = ClosedLoopRequest(A=ns.A, B=ns.B, C=ns.C, K=ns.K, L=ns.L, out=ns.out)
        out = app.run(req)

    elif ns.cmd == "k0":
        for k in ("A","B","C","K"):
            if getattr(ns, k) is None:
                parser.error(f"--{k} is required")
        req = K0Request(A=ns.A, B=ns.B, C=ns.C, K=ns.K, L=ns.L, mode=ns.mode,
                        ogata_extra_gain=ns.ogata_extra_gain, out=ns.out)
        out = app.run(req)

    elif ns.cmd == "select":
        for k in ("A","B","C","K"):
            if getattr(ns, k) is None:
                parser.error(f"--{k} is required")
        req = SelectRequest(A=ns.A, B=ns.B, C=ns.C, K=ns.K, method=ns.method,
                            rule_of_thumb=ns.rule_of_thumb, speedup=ns.speedup,
                            sweep=ns.sweep, steps=ns.steps, dlqe=ns.dlqe,
                            G=ns.G, Qn=ns.Qn, Rn=ns.Rn, csv=ns.csv, out=ns.out)
        out = app.run(req)

    elif ns.cmd == "sim":
        for k in ("A","B","C","K","L"):
            if getattr(ns, k) is None:
                parser.error(f"--{k} is required")
        req = SimRequest(A=ns.A, B=ns.B, C=ns.C, K=ns.K, L=ns.L, N=ns.N, Ts=ns.Ts,
                         ref=ns.ref, K0=ns.K0, k0_mode=ns.k0_mode, ogata_extra_gain=ns.ogata_extra_gain,
                         csv=ns.csv, out=ns.out, plot=ns.plot, plot_type=ns.plot_type, plotly=ns.plotly, html=ns.html)
        out = app.run(req)

    elif ns.cmd == "example":
        req = ExampleRequest(which=ns.which, Ts=ns.Ts)
        out = app.run(req)
    else:
        parser.error("Unknown command")

    # print compact JSON to stdout
    import json
    print(json.dumps(out, default=str, indent=2))


if __name__ == "__main__":
    main()
