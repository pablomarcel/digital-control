#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Public API functions for the model_predictive_control package."""

from pathlib import Path
from typing import Any

try:
    from .app import MPCApp, MPCRunResult
    from .core import LinearMPCProblem, parse_problem, run_spec, simulate_mpc, solve_open_loop
except ImportError:  # pragma: no cover
    from app import MPCApp, MPCRunResult  # type: ignore
    from core import LinearMPCProblem, parse_problem, run_spec, simulate_mpc, solve_open_loop  # type: ignore


def run_mpc_file(input_path: str | Path, out_dir: str | Path | None = None, *, plots: bool = True, show: bool = False) -> MPCRunResult:
    """Run an MPC JSON file through the package application."""

    return MPCApp(out_dir=out_dir).run_file(input_path, plots=plots, show=show)


def run_mpc_spec(spec: dict[str, Any], out_dir: str | Path | None = None, *, plots: bool = True, show: bool = False) -> MPCRunResult:
    """Run an in-memory MPC specification through the package application."""

    return MPCApp(out_dir=out_dir).run_spec(spec, plots=plots, show=show)


__all__ = [
    "LinearMPCProblem",
    "MPCApp",
    "MPCRunResult",
    "parse_problem",
    "run_mpc_file",
    "run_mpc_spec",
    "run_spec",
    "simulate_mpc",
    "solve_open_loop",
]
