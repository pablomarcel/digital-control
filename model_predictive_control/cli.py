#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Command-line entry point for model_predictive_control."""

import argparse
import json
import sys
from pathlib import Path

# Import shim so these styles can work depending on where the runbook is used:
#   python -m cli ...
#   python -m model_predictive_control.cli ...
#   python model_predictive_control/cli.py ...
if __package__ in (None, ""):
    PACKAGE_DIR = Path(__file__).resolve().parent
    PARENT = PACKAGE_DIR.parent
    if str(PARENT) not in sys.path:
        sys.path.insert(0, str(PARENT))
    from model_predictive_control.app import MPCApp  # type: ignore
    from model_predictive_control.utils import optional_import, print_kv, resolve_project_paths  # type: ignore
else:
    from .app import MPCApp
    from .utils import optional_import, print_kv, resolve_project_paths


EXAMPLE_FILES = {
    "double_integrator_mpc.json": {
        "title": "Double integrator constrained MPC",
        "analysis_type": "lti_mpc_sim",
        "plant": "linear_state_space",
        "solver": {"backend": "native_slsqp", "maxiter": 250, "ftol": 1e-8},
        "dt": 0.1,
        "model": {
            "A": [[1.0, 0.1], [0.0, 1.0]],
            "B": [[0.005], [0.1]],
            "d": [0.0, 0.0]
        },
        "state_names": ["position", "velocity"],
        "input_names": ["acceleration_command"],
        "x0": [6.0, 0.0],
        "x_ref": [0.0, 0.0],
        "u_ref": [0.0],
        "horizon": 18,
        "steps": 70,
        "weights": {
            "Q": [8.0, 0.8],
            "R": [0.04],
            "P": [20.0, 3.0],
            "Rd": [0.15]
        },
        "constraints": {
            "u_min": [-2.0],
            "u_max": [2.0],
            "du_min": [-0.45],
            "du_max": [0.45],
            "x_min": [-10.0, -5.0],
            "x_max": [10.0, 5.0]
        }
    },
    "double_integrator_mpc_casadi.json": {
        "title": "Double integrator constrained MPC - CasADi Opti backend",
        "analysis_type": "lti_mpc_sim",
        "plant": "linear_state_space",
        "solver": {
            "backend": "casadi_opti",
            "max_iter": 150,
            "tol": 1e-8,
            "acceptable_tol": 1e-6,
            "print_level": 0,
            "print_time": False,
            "expand": False
        },
        "dt": 0.1,
        "model": {
            "A": [[1.0, 0.1], [0.0, 1.0]],
            "B": [[0.005], [0.1]],
            "d": [0.0, 0.0]
        },
        "state_names": ["position", "velocity"],
        "input_names": ["acceleration_command"],
        "x0": [6.0, 0.0],
        "x_ref": [0.0, 0.0],
        "u_ref": [0.0],
        "horizon": 14,
        "steps": 45,
        "weights": {
            "Q": [8.0, 0.8],
            "R": [0.04],
            "P": [20.0, 3.0],
            "Rd": [0.15]
        },
        "constraints": {
            "u_min": [-2.0],
            "u_max": [2.0],
            "du_min": [-0.45],
            "du_max": [0.45],
            "x_min": [-10.0, -5.0],
            "x_max": [10.0, 5.0]
        }
    },
    "automotive_engine_cooling_mpc.json": {
        "title": "Automotive engine cooling LTV MPC demo",
        "analysis_type": "ltv_mpc_sim",
        "plant": "thermal_cooling_4state_demo",
        "solver": {"backend": "native_slsqp", "maxiter": 250, "ftol": 1e-8},
        "dt": 1.0,
        "horizon": 12,
        "steps": 90,
        "ambient_temp_c": 38.0,
        "x0": [118.0, 101.0, 110.0, 90.0],
        "x_ref": [105.0, 92.0, 100.0, 82.0],
        "state_names": ["wall_temp_c", "coolant_out_c", "block_temp_c", "radiator_out_c"],
        "input_names": ["pump_command", "fan_command"],
        "weights": {
            "Q": [5.0, 8.0, 2.0, 1.0],
            "R": [0.05, 0.08],
            "P": [10.0, 14.0, 4.0, 2.0],
            "Rd": [0.35, 0.45]
        },
        "constraints": {
            "u_min": [0.0, 0.0],
            "u_max": [1.0, 1.0],
            "du_min": [-0.12, -0.12],
            "du_max": [0.12, 0.12],
            "x_min": [70.0, 60.0, 70.0, 50.0],
            "x_max": [128.0, 112.0, 122.0, 108.0]
        }
    },
    "automotive_engine_cooling_mpc_casadi.json": {
        "title": "Automotive engine cooling LTV MPC demo - CasADi Opti backend",
        "analysis_type": "ltv_mpc_sim",
        "plant": "thermal_cooling_4state_demo",
        "solver": {
            "backend": "casadi_opti",
            "max_iter": 150,
            "tol": 1e-8,
            "acceptable_tol": 1e-6,
            "print_level": 0,
            "print_time": False,
            "expand": False
        },
        "dt": 1.0,
        "horizon": 8,
        "steps": 45,
        "ambient_temp_c": 38.0,
        "x0": [118.0, 101.0, 110.0, 90.0],
        "x_ref": [105.0, 92.0, 100.0, 82.0],
        "state_names": ["wall_temp_c", "coolant_out_c", "block_temp_c", "radiator_out_c"],
        "input_names": ["pump_command", "fan_command"],
        "weights": {
            "Q": [5.0, 8.0, 2.0, 1.0],
            "R": [0.05, 0.08],
            "P": [10.0, 14.0, 4.0, 2.0],
            "Rd": [0.35, 0.45]
        },
        "constraints": {
            "u_min": [0.0, 0.0],
            "u_max": [1.0, 1.0],
            "du_min": [-0.12, -0.12],
            "du_max": [0.12, 0.12],
            "x_min": [70.0, 60.0, 70.0, 50.0],
            "x_max": [128.0, 112.0, 122.0, 108.0]
        }
    }
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="model_predictive_control",
        description="Run small discrete-time MPC experiments from JSON input files.",
    )
    sub = parser.add_subparsers(dest="command")

    p_run = sub.add_parser("run", help="Run one MPC JSON input file")
    p_run.add_argument("input", help="Input JSON path or filename in the package in directory")
    p_run.add_argument("--out", default=None, help="Output directory. Defaults to package out directory")
    p_run.add_argument("--stem", default=None, help="Output filename stem")
    p_run.add_argument("--no-plots", action="store_true", help="Disable Matplotlib plot generation")
    p_run.add_argument("--show", action="store_true", help="Show plots interactively")

    p_init = sub.add_parser("init-examples", help="Write example JSON input files into package/in")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing examples")

    sub.add_parser("list-examples", help="List example JSON files")
    sub.add_parser("check-libs", help="Check optional MPC-related package imports")
    sub.add_parser("tree", help="Print resolved package input and output folders")
    sub.add_parser("self-test", help="Create examples and run the native double-integrator demo")
    sub.add_parser("self-test-casadi", help="Create examples and run the CasADi double-integrator demo")

    return parser


def cmd_init_examples(force: bool = False) -> int:
    paths = resolve_project_paths()
    created = []
    for name, payload in EXAMPLE_FILES.items():
        path = paths.in_dir / name
        if path.exists() and not force:
            continue
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            f.write("\n")
        created.append(path)
    if created:
        print("Created example input files:")
        for path in created:
            print(f"  {path}")
    else:
        print("Example input files already exist. Use --force to overwrite.")
    return 0


def cmd_list_examples() -> int:
    paths = resolve_project_paths()
    print("Built-in examples:")
    for name in EXAMPLE_FILES:
        status = "exists" if (paths.in_dir / name).exists() else "not written yet"
        print(f"  {name} ({status})")
    return 0


def cmd_check_libs() -> int:
    modules = ["numpy", "scipy", "control", "gekko", "do_mpc", "nmpyc", "mpcrl", "casadi", "ltv_mpc"]
    rows = [optional_import(name) for name in modules]
    for ok, message in rows:
        prefix = "OK" if ok else "--"
        print(f"{prefix} {message}")
    return 0


def cmd_tree() -> int:
    paths = resolve_project_paths()
    print_kv([
        ("package_dir", paths.package_dir),
        ("input_dir", paths.in_dir),
        ("output_dir", paths.out_dir),
    ])
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    app = MPCApp(out_dir=args.out)
    run = app.run_file(args.input, stem=args.stem, plots=not args.no_plots, show=args.show)
    result = run.result
    print("MPC run complete.")
    print_kv([
        ("title", result.get("title")),
        ("plant", result.get("plant")),
        ("solver_backend", result.get("solver_backend")),
        ("steps", result.get("steps")),
        ("horizon", result.get("horizon")),
        ("all_success", result.get("all_optimizations_successful")),
        ("final_state", result.get("final_state")),
    ])
    print("Files:")
    for label, path in run.files.items():
        print(f"  {label}: {path}")
    return 0


def cmd_self_test() -> int:
    cmd_init_examples(force=False)
    paths = resolve_project_paths()
    args = argparse.Namespace(input=str(paths.in_dir / "double_integrator_mpc.json"), out=None, stem="self_test_double_integrator", no_plots=False, show=False)
    return cmd_run(args)


def cmd_self_test_casadi() -> int:
    cmd_init_examples(force=False)
    paths = resolve_project_paths()
    args = argparse.Namespace(input=str(paths.in_dir / "double_integrator_mpc_casadi.json"), out=None, stem="self_test_double_integrator_casadi", no_plots=False, show=False)
    return cmd_run(args)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0
    if args.command == "init-examples":
        return cmd_init_examples(force=args.force)
    if args.command == "list-examples":
        return cmd_list_examples()
    if args.command == "check-libs":
        return cmd_check_libs()
    if args.command == "tree":
        return cmd_tree()
    if args.command == "run":
        return cmd_run(args)
    if args.command == "self-test":
        return cmd_self_test()
    if args.command == "self-test-casadi":
        return cmd_self_test_casadi()

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
