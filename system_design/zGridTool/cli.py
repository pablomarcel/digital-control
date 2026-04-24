# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, os, sys

# ---------- Import shim so `python cli.py` works with absolute imports ----------
if __package__ in (None, ""):
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    from system_design.zGridTool.apis import RunRequest
    from system_design.zGridTool.app import ZGridApp
    from system_design.zGridTool.io import parse_num_list
else:
    from .apis import RunRequest
    from .app import ZGridApp
    from .io import parse_num_list

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="z-grid tool (OOP) with MPL/Plotly backends.",
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    gT = p.add_mutually_exclusive_group(required=True)
    gT.add_argument("--T", type=float, help="Sampling period [s]")
    gT.add_argument("--fs", type=float, help="Sampling frequency [Hz] (overrides T=1/fs)")

    p.add_argument("--zetas", nargs="+", default=["0.1","0.2","0.3","0.4","0.6","0.8"])
    p.add_argument("--wd_over_ws", nargs="+", default=["0","0.1","0.2","0.25","0.3","0.4","0.5"])
    p.add_argument("--wnT", nargs="+", default=["0.5","1.0","1.5","2.0"])
    p.add_argument("--theta_max", type=float, default=3.141592653589793)
    p.add_argument("--settling_sigma", type=float, default=None)

    p.add_argument("--pz", nargs="*", default=[])

    p.add_argument("--backend", choices=("mpl","plotly"), default="mpl")
    p.add_argument("--png", default="zgrid.png")
    p.add_argument("--plotly", dest="plotly_html", default=None)
    p.add_argument("--width", type=int, default=900)
    p.add_argument("--height", type=int, default=900)
    p.add_argument("--dpi", type=int, default=150)
    p.add_argument("--dark", action="store_true")
    p.add_argument("--theme", choices=("plotly_white","plotly_dark","plotly"), default="plotly_white")
    p.add_argument("--legend_mode", choices=("minimal","full"), default="minimal")
    p.add_argument("--legend_loc", choices=("bottom","top","right","inside"), default="bottom")
    p.add_argument("--title", default="z-plane design grid")
    p.add_argument("--title_mode", choices=("auto","minimal","full"), default="auto")
    p.add_argument("--responsive", dest="responsive", action="store_true")
    p.add_argument("--fixed_size", dest="responsive", action="store_false")
    p.set_defaults(responsive=True)

    p.add_argument("--export_csv_prefix", default=None)
    p.add_argument("--verbose", action="store_true")
    return p

def main(argv=None):
    args = build_parser().parse_args(argv)
    req = RunRequest(
        T=args.T, fs=args.fs,
        zetas=parse_num_list(args.zetas),
        wd_over_ws=parse_num_list(args.wd_over_ws),
        wnT=parse_num_list(args.wnT),
        theta_max=float(args.theta_max),
        settling_sigma=args.settling_sigma,
        pz_files=args.pz,
        backend=args.backend,
        png=args.png,
        plotly_html=args.plotly_html,
        width=args.width,
        height=args.height,
        dpi=args.dpi,
        dark=args.dark,
        theme=args.theme,
        legend_mode=args.legend_mode,
        legend_loc=args.legend_loc,
        title=args.title,
        title_mode=args.title_mode,
        responsive=bool(args.responsive),
        export_csv_prefix=args.export_csv_prefix,
        verbose=args.verbose,
    )
    app = ZGridApp()
    res = app.run(req)
    if res.png_path: print(f"PNG: {res.png_path}")
    if res.html_path: print(f"HTML: {res.html_path}")
    if res.csv_prefix: print(f"CSV prefix: {res.csv_prefix}")

if __name__ == "__main__":
    main()
