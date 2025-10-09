from __future__ import annotations

# --- dual-mode imports: script (python cli.py) and module (-m quadraticControl.quadraticTool.cli) ---
try:
    # package execution
    from .apis import RunRequest
    from .app import QuadraticApp
    from .utils import out_path, setup_logging
except Exception:
    # script execution fallback
    import sys
    from pathlib import Path

    here = Path(__file__).resolve()
    project_root = here.parents[2]  # <repo-root>/
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from quadraticControl.quadraticTool.apis import RunRequest
    from quadraticControl.quadraticTool.app import QuadraticApp
    from quadraticControl.quadraticTool.utils import out_path, setup_logging

import argparse
import sys as _sys
from typing import Dict


def _parse_params(pairs: list[str] | None) -> Dict[str, float]:
    """Parse ['k=v', 'a=1.2'] -> {'k': 1.2, ...}; ignore malformed entries."""
    params: Dict[str, float] = {}
    if not pairs:
        return params
    for item in pairs:
        if "=" not in item:
            continue
        k, v = item.split("=", 1)
        k = k.strip()
        try:
            params[k] = float(v)
        except ValueError:
            # keep forgiving; YAML is source of truth
            continue
    return params


def build_parser() -> argparse.ArgumentParser:
    # Common options for all subcommands
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--outdir",
        "-o",
        default=out_path(),  # package default out/
        help="Base output directory (default: package out/)",
    )

    parser = argparse.ArgumentParser(
        prog="quadraticControl.quadraticTool",
        description="Quadratic optimal control utilities",
        allow_abbrev=False,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # YAML-driven run (mode comes from YAML)
    p_solve = sub.add_parser(
        "solve",
        help="Run using a YAML infile (mode specified in the YAML)",
        parents=[common],
        add_help=True,
    )
    p_solve.add_argument("--infile", "-i", required=True, help="Path to YAML config file")
    p_solve.add_argument("--name", "-n", required=True, help="Case name (output folder name)")
    p_solve.add_argument(
        "--plot",
        choices=("none", "mpl", "plotly"),
        default="none",
        help="Optional plot output (default: none)",
    )
    p_solve.add_argument(
        "--param",
        "-p",
        action="append",
        default=[],
        help="Override YAML params as key=value (repeatable)",
    )
    p_solve.add_argument(
        "--sweep",
        help="Optional sweep spec 'name=start:stop:points' (overrides YAML sweep if given)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    setup_logging("INFO")
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "solve":
        params = _parse_params(args.param)
        # req.mode is only a fallback; YAML's `mode` takes precedence.
        req = RunRequest(
            mode="fh-dt",
            infile=args.infile,
            name=args.name,
            outdir=args.outdir,
            plot=args.plot,
            params=params,
            sweep=args.sweep,
        )
        out_case = QuadraticApp().run(req)
        print(out_case)
        return 0

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    _sys.exit(main())
