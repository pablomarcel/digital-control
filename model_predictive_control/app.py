#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Application orchestration for model_predictive_control."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from .core import run_spec
    from .in_out import read_input, save_all
    from .utils import safe_slug
except ImportError:  # pragma: no cover
    from core import run_spec  # type: ignore
    from in_out import read_input, save_all  # type: ignore
    from utils import safe_slug  # type: ignore


@dataclass
class MPCRunResult:
    """High-level application result."""

    result: dict[str, Any]
    files: dict[str, Path]


class MPCApp:
    """Small application object for running MPC studies."""

    def __init__(self, out_dir: str | Path | None = None) -> None:
        self.out_dir = Path(out_dir).expanduser().resolve() if out_dir else None

    def run_file(self, input_path: str | Path, *, stem: str | None = None, plots: bool = True, show: bool = False) -> MPCRunResult:
        """Run one JSON input file and save outputs."""

        spec = read_input(input_path)
        result = run_spec(spec)
        resolved_stem = stem or safe_slug(str(spec.get("title", Path(input_path).stem)))
        files = save_all(result, out_dir=self.out_dir, stem=resolved_stem, make_plots=plots, show=show)
        return MPCRunResult(result=result, files=files)

    def run_spec(self, spec: dict[str, Any], *, stem: str | None = None, plots: bool = True, show: bool = False) -> MPCRunResult:
        """Run one in-memory MPC specification and save outputs."""

        result = run_spec(spec)
        resolved_stem = stem or safe_slug(str(spec.get("title", "mpc_run")))
        files = save_all(result, out_dir=self.out_dir, stem=resolved_stem, make_plots=plots, show=show)
        return MPCRunResult(result=result, files=files)
