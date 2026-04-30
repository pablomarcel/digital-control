#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Input, output, and plotting helpers for MPC runs."""

from pathlib import Path
from typing import Any

import numpy as np

try:
    from .utils import load_json, save_json, safe_slug, to_jsonable, resolve_project_paths
except ImportError:  # pragma: no cover
    from utils import load_json, save_json, safe_slug, to_jsonable, resolve_project_paths  # type: ignore


def read_input(path: str | Path) -> dict[str, Any]:
    """Read an MPC input specification from JSON."""

    return load_json(path)


def write_result(result: dict[str, Any], out_dir: str | Path | None = None, stem: str | None = None) -> dict[str, Path]:
    """Write JSON and CSV outputs for one MPC result."""

    paths = resolve_project_paths(out_dir)
    title = stem or safe_slug(str(result.get("title", "mpc_run")))
    json_path = paths.out_dir / f"{title}_results.json"
    save_json(result, json_path)

    state_csv = paths.out_dir / f"{title}_states.csv"
    input_csv = paths.out_dir / f"{title}_inputs.csv"
    _write_states_csv(result, state_csv)
    _write_inputs_csv(result, input_csv)

    return {"json": json_path, "states_csv": state_csv, "inputs_csv": input_csv}


def _write_states_csv(result: dict[str, Any], path: Path) -> None:
    time = np.asarray(result["time"], dtype=float)
    X = np.asarray(result["X"], dtype=float)
    Xref = np.asarray(result.get("x_ref", np.zeros_like(X)), dtype=float)
    names = list(result.get("state_names") or [f"x{i + 1}" for i in range(X.shape[1])])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        header = ["time"] + names + [f"{name}_ref" for name in names]
        f.write(",".join(header) + "\n")
        for k in range(X.shape[0]):
            row = [time[k], *X[k], *Xref[k]]
            f.write(",".join(f"{v:.12g}" for v in row) + "\n")


def _write_inputs_csv(result: dict[str, Any], path: Path) -> None:
    time = np.asarray(result["time_u"], dtype=float)
    U = np.asarray(result["U"], dtype=float)
    Uref = np.asarray(result.get("u_ref", np.zeros_like(U)), dtype=float)
    names = list(result.get("input_names") or [f"u{i + 1}" for i in range(U.shape[1])])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        header = ["time"] + names + [f"{name}_ref" for name in names]
        f.write(",".join(header) + "\n")
        for k in range(U.shape[0]):
            row = [time[k], *U[k], *Uref[k]]
            f.write(",".join(f"{v:.12g}" for v in row) + "\n")


def plot_result(result: dict[str, Any], out_dir: str | Path | None = None, stem: str | None = None, show: bool = False) -> dict[str, Path]:
    """Create Matplotlib plots for states, inputs, and objective history."""

    import matplotlib.pyplot as plt

    paths = resolve_project_paths(out_dir)
    title = stem or safe_slug(str(result.get("title", "mpc_run")))
    output: dict[str, Path] = {}

    time = np.asarray(result["time"], dtype=float)
    time_u = np.asarray(result["time_u"], dtype=float)
    X = np.asarray(result["X"], dtype=float)
    U = np.asarray(result["U"], dtype=float)
    Xref = np.asarray(result.get("x_ref", np.zeros_like(X)), dtype=float)
    costs = np.asarray(result.get("costs", []), dtype=float)
    state_names = list(result.get("state_names") or [f"x{i + 1}" for i in range(X.shape[1])])
    input_names = list(result.get("input_names") or [f"u{i + 1}" for i in range(U.shape[1])])

    fig, ax = plt.subplots(figsize=(10, 6))
    for i, name in enumerate(state_names):
        ax.plot(time, X[:, i], label=name)
        ax.plot(time, Xref[:, i], linestyle="--", label=f"{name} ref")
    ax.set_title(f"{result.get('title', 'MPC run')} - states")
    ax.set_xlabel("time")
    ax.set_ylabel("state value")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path = paths.out_dir / f"{title}_states.png"
    fig.savefig(path, dpi=160)
    output["states_plot"] = path
    if show:
        plt.show()
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    for i, name in enumerate(input_names):
        ax.step(time_u, U[:, i], where="post", label=name)
    ax.set_title(f"{result.get('title', 'MPC run')} - control inputs")
    ax.set_xlabel("time")
    ax.set_ylabel("input value")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path = paths.out_dir / f"{title}_inputs.png"
    fig.savefig(path, dpi=160)
    output["inputs_plot"] = path
    if show:
        plt.show()
    plt.close(fig)

    if costs.size:
        fig, ax = plt.subplots(figsize=(10, 4.8))
        ax.plot(time_u, costs)
        ax.set_title(f"{result.get('title', 'MPC run')} - horizon objective")
        ax.set_xlabel("time")
        ax.set_ylabel("objective")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        path = paths.out_dir / f"{title}_cost.png"
        fig.savefig(path, dpi=160)
        output["cost_plot"] = path
        if show:
            plt.show()
        plt.close(fig)

    return output


def save_all(result: dict[str, Any], out_dir: str | Path | None = None, stem: str | None = None, make_plots: bool = True, show: bool = False) -> dict[str, Path]:
    """Save JSON, CSV, and optional plot outputs."""

    written = write_result(result, out_dir=out_dir, stem=stem)
    if make_plots:
        written.update(plot_result(result, out_dir=out_dir, stem=stem, show=show))
    return written
