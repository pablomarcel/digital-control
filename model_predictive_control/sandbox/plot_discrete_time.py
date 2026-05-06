#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
plot_discrete_time.py

Standalone plotting sandbox for Rawlings Section 1.2.4 / equation (1.4)
outputs.

This script is designed for the actual project layout:

    digitalControl/
      model_predictive_control/
        RUNS.md
        sandbox/
          discrete_time_system.py
          plot_discrete_time.py
          out/
            discrete_time_system/
              double_integrator_step.csv
              double_integrator_step.json

Typical RUNS.md commands, executed from inside model_predictive_control:

    python sandbox/plot_discrete_time.py \
      sandbox/out/discrete_time_system/double_integrator_step.csv

Convenience resolver:

    python sandbox/plot_discrete_time.py \
      out/discrete_time_system/double_integrator_step.csv

The second command also works. If the input is not found exactly as typed,
the resolver checks the sandbox output folder before failing. This lets the
RUNS.md stay clean while still keeping sandbox artifacts under sandbox/out.

Outputs are saved next to the resolved input file by default, for example:

    sandbox/out/discrete_time_system/double_integrator_step_xk.png

Supported input formats:
- CSV with columns k, x1, x2, ... and optional u1, u2, ...
- JSON containing one trajectory key such as X_analytical_eq_1_4, X_recursive,
  X_condensed_prediction_matrix, or X.
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np


MATLAB_COLORS = [
    "#0072BD",  # blue
    "#D95319",  # orange
    "#EDB120",  # yellow
    "#7E2F8E",  # purple
    "#77AC30",  # green
    "#4DBEEE",  # cyan
    "#A2142F",  # red
]


# -----------------------------------------------------------------------------
# Project-path helpers
# -----------------------------------------------------------------------------


def script_path() -> Path:
    """Return this script path, resolved."""

    return Path(__file__).expanduser().resolve()


def sandbox_dir() -> Path:
    """Return the sandbox directory containing this script."""

    return script_path().parent


def package_dir() -> Path:
    """Return the model_predictive_control package directory."""

    # In the intended layout, this file lives in model_predictive_control/sandbox.
    return sandbox_dir().parent


def unique_existing_file(candidates: list[Path]) -> Path | None:
    """Return the first existing file from a candidate list."""

    seen: set[Path] = set()
    for item in candidates:
        try:
            resolved = item.expanduser().resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            return resolved
    return None


def resolve_input_path(path_or_name: str | Path) -> Path:
    """Resolve an input file from RUNS.md-friendly paths.

    The common mistake this prevents is passing:

        out/discrete_time_system/double_integrator_step.csv

    while the actual sandbox output is located at:

        sandbox/out/discrete_time_system/double_integrator_step.csv

    The resolver checks exact paths first, then sandbox-aware alternatives.
    """

    raw = Path(path_or_name).expanduser()
    cwd = Path.cwd().resolve()
    pkg = package_dir()
    sbox = sandbox_dir()

    candidates: list[Path] = []

    # 1) Exact user spelling from current working directory or absolute path.
    candidates.append(raw)
    if not raw.is_absolute():
        candidates.extend([
            cwd / raw,
            pkg / raw,
            sbox / raw,
        ])

    # 2) Sandbox-aware correction for paths like out/discrete_time_system/file.csv.
    parts = raw.parts
    if parts and parts[0] == "out":
        tail = Path(*parts[1:]) if len(parts) > 1 else Path()
        candidates.extend([
            sbox / "out" / tail,
            pkg / "sandbox" / "out" / tail,
            cwd / "sandbox" / "out" / tail,
        ])

    # 3) If only a filename is passed, search the known output folders.
    if len(parts) == 1:
        candidates.extend([
            sbox / "out" / raw.name,
            sbox / "out" / "discrete_time_system" / raw.name,
            pkg / "out" / raw.name,
            pkg / "out" / "discrete_time_system" / raw.name,
            pkg / "sandbox" / "out" / raw.name,
            pkg / "sandbox" / "out" / "discrete_time_system" / raw.name,
        ])

    found = unique_existing_file(candidates)
    if found is not None:
        return found

    searched = []
    seen_text: set[str] = set()
    for item in candidates:
        text = str(item)
        if text not in seen_text:
            searched.append(text)
            seen_text.add(text)

    raise FileNotFoundError(
        "Input file not found.\n"
        f"Requested: {path_or_name}\n"
        "Searched:\n  " + "\n  ".join(searched)
    )


def resolve_output_path(input_path: Path, out: str | None, fmt: str) -> Path:
    """Resolve the output plot path.

    If --out is omitted, save next to the resolved input file. If --out is a
    directory or has no suffix, create ``<input_stem>_xk.<format>`` inside it.
    Relative --out paths are interpreted from the current working directory so
    RUNS.md commands remain predictable.
    """

    if not out:
        return (input_path.parent / f"{input_path.stem}_xk.{fmt}").resolve()

    candidate = Path(out).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate

    if candidate.suffix:
        return candidate.resolve()

    candidate.mkdir(parents=True, exist_ok=True)
    return (candidate / f"{input_path.stem}_xk.{fmt}").resolve()


# -----------------------------------------------------------------------------
# Readers
# -----------------------------------------------------------------------------


def natural_key(name: str) -> tuple[str, int]:
    """Sort x1, x2, ..., x10 in natural engineering order."""

    prefix = "".join(ch for ch in name if not ch.isdigit())
    digits = "".join(ch for ch in name if ch.isdigit())
    number = int(digits) if digits else -1
    return prefix, number


def read_csv_xk(path: Path) -> tuple[np.ndarray, np.ndarray, list[str], np.ndarray | None, list[str]]:
    """Read k, x columns, and optional u columns from a sandbox CSV file."""

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"CSV file has no header: {path}")
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    if not rows:
        raise ValueError(f"CSV file has no data rows: {path}")

    if "k" not in fieldnames:
        raise ValueError("CSV must contain a 'k' column.")

    state_names = sorted(
        [name for name in fieldnames if name.startswith("x") and name[1:].isdigit()],
        key=natural_key,
    )
    input_names = sorted(
        [name for name in fieldnames if name.startswith("u") and name[1:].isdigit()],
        key=natural_key,
    )

    if not state_names:
        raise ValueError("CSV must contain state columns named x1, x2, ...")

    k_values: list[float] = []
    x_rows: list[list[float]] = []
    u_rows: list[list[float]] = []

    for row in rows:
        k_values.append(float(row["k"]))
        x_rows.append([float(row[name]) for name in state_names])

        if input_names:
            values: list[float] = []
            for name in input_names:
                raw_value = row.get(name, "")
                try:
                    values.append(float(raw_value))
                except (TypeError, ValueError):
                    values.append(np.nan)
            u_rows.append(values)

    k = np.asarray(k_values, dtype=float)
    x = np.asarray(x_rows, dtype=float)
    u = np.asarray(u_rows, dtype=float) if input_names else None
    return k, x, state_names, u, input_names


def read_json_xk(path: Path) -> tuple[np.ndarray, np.ndarray, list[str], np.ndarray | None, list[str]]:
    """Read x(k) and optional u(k) from a sandbox JSON result file."""

    with path.open("r", encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    candidates = [
        "X_analytical_eq_1_4",
        "X_recursive",
        "X_condensed_prediction_matrix",
        "X",
        "states",
    ]

    x_data: Any | None = None
    source_name = ""
    for key in candidates:
        if key in data:
            x_data = data[key]
            source_name = key
            break

    if x_data is None:
        raise ValueError("JSON must contain one of: " + ", ".join(candidates))

    x = np.asarray(x_data, dtype=float)
    if x.ndim != 2:
        raise ValueError(f"JSON trajectory {source_name!r} must be 2-D; got shape {x.shape}")

    k = np.asarray(data.get("k", np.arange(x.shape[0])), dtype=float)
    if k.ndim != 1 or k.size != x.shape[0]:
        k = np.arange(x.shape[0], dtype=float)

    state_names = data.get("state_names")
    if isinstance(state_names, list) and len(state_names) == x.shape[1]:
        state_labels = [str(name) for name in state_names]
    else:
        state_labels = [f"x{i + 1}" for i in range(x.shape[1])]

    u = None
    input_labels: list[str] = []
    for key in ("U", "u", "inputs"):
        if key in data:
            u = np.asarray(data[key], dtype=float)
            if u.ndim == 1:
                u = u.reshape(-1, 1)
            if u.ndim == 2:
                names = data.get("input_names")
                if isinstance(names, list) and len(names) == u.shape[1]:
                    input_labels = [str(name) for name in names]
                else:
                    input_labels = [f"u{i + 1}" for i in range(u.shape[1])]
            else:
                u = None
            break

    return k, x, state_labels, u, input_labels


def read_xk(path: Path) -> tuple[np.ndarray, np.ndarray, list[str], np.ndarray | None, list[str]]:
    """Dispatch reader based on file extension."""

    suffix = path.suffix.lower()
    if suffix == ".csv":
        return read_csv_xk(path)
    if suffix == ".json":
        return read_json_xk(path)
    raise ValueError(f"Unsupported input type {suffix!r}. Use .csv or .json")


# -----------------------------------------------------------------------------
# Plotting
# -----------------------------------------------------------------------------


def apply_matlabish_axes(ax: Any, *, title: str, xlabel: str, ylabel: str) -> None:
    """Apply a compact MATLAB-like axes style."""

    ax.set_title(title, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, which="major", linestyle="-", linewidth=0.6, alpha=0.35)
    ax.minorticks_on()
    ax.grid(True, which="minor", linestyle=":", linewidth=0.4, alpha=0.18)
    ax.tick_params(direction="in", top=True, right=True)
    for spine in ax.spines.values():
        spine.set_linewidth(0.8)


def draw_state_series(ax: Any, k: np.ndarray, x: np.ndarray, state_names: list[str], style: str) -> None:
    """Draw state trajectories using the selected discrete-time style."""

    for i, name in enumerate(state_names):
        color = MATLAB_COLORS[i % len(MATLAB_COLORS)]
        if style == "stem":
            markerline, stemlines, baseline = ax.stem(
                k,
                x[:, i],
                linefmt="-",
                markerfmt="o",
                basefmt="k-",
            )
            markerline.set_markerfacecolor("none")
            markerline.set_markeredgecolor(color)
            markerline.set_color(color)
            stemlines.set_color(color)
            stemlines.set_linewidth(1.1)
            baseline.set_linewidth(0.8)
            markerline.set_label(name)
        elif style == "stairs":
            ax.step(k, x[:, i], where="post", linewidth=1.7, color=color, label=name)
            ax.plot(k, x[:, i], "o", markersize=4.0, markerfacecolor="none", color=color)
        else:
            ax.plot(
                k,
                x[:, i],
                "-o",
                linewidth=1.7,
                markersize=4.0,
                markerfacecolor="none",
                color=color,
                label=name,
            )


def draw_input_series(ax: Any, u: np.ndarray, input_names: list[str], color_offset: int) -> None:
    """Draw input trajectories as zero-order-hold stairs."""

    ku = np.arange(u.shape[0], dtype=float)
    for i, name in enumerate(input_names):
        color = MATLAB_COLORS[(i + color_offset) % len(MATLAB_COLORS)]
        ax.step(ku, u[:, i], where="post", linewidth=1.7, color=color, label=name)
        ax.plot(ku, u[:, i], "o", markersize=3.5, markerfacecolor="none", color=color)


def plot_xk(
    *,
    k: np.ndarray,
    x: np.ndarray,
    state_names: list[str],
    u: np.ndarray | None,
    input_names: list[str],
    output_path: Path,
    title: str,
    style: str,
    include_input: bool,
    show: bool,
) -> None:
    """Create the MATLAB-style x(k) plot."""

    import matplotlib.pyplot as plt

    output_path.parent.mkdir(parents=True, exist_ok=True)

    has_input = include_input and u is not None and bool(input_names)
    if has_input:
        fig, axes = plt.subplots(2, 1, figsize=(10.5, 7.2), sharex=False)
        ax_x, ax_u = axes
    else:
        fig, ax_x = plt.subplots(1, 1, figsize=(10.5, 5.8))
        ax_u = None

    draw_state_series(ax_x, k, x, state_names, style)
    apply_matlabish_axes(
        ax_x,
        title=title,
        xlabel="sample index, k",
        ylabel="state, x(k)",
    )
    ax_x.legend(loc="best", frameon=True)

    if has_input and ax_u is not None and u is not None:
        draw_input_series(ax_u, u, input_names, color_offset=x.shape[1])
        apply_matlabish_axes(
            ax_u,
            title="Input sequence",
            xlabel="sample index, k",
            ylabel="input, u(k)",
        )
        ax_u.legend(loc="best", frameon=True)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(
        description="Create a MATLAB-style plot of x(k) from a discrete-time sandbox CSV/JSON output."
    )
    parser.add_argument(
        "input",
        help=(
            "Path to a CSV/JSON output. Supports exact paths and the shortcut "
            "out/discrete_time_system/<file>, which resolves to sandbox/out/... when needed."
        ),
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output PNG/PDF/SVG path or output directory. Defaults next to the resolved input file.",
    )
    parser.add_argument(
        "--format",
        default="png",
        choices=["png", "pdf", "svg"],
        help="Plot format used when --out is a directory or omitted.",
    )
    parser.add_argument(
        "--style",
        default="line",
        choices=["line", "stem", "stairs"],
        help="Plot style. 'line' is MATLAB plot-like; 'stem' emphasizes discrete samples.",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Optional custom plot title.",
    )
    parser.add_argument(
        "--no-input",
        action="store_true",
        help="Only plot x(k); do not include u(k) subplot even if input data exists.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show the plot interactively after saving it.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the plotting command."""

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        input_path = resolve_input_path(args.input)
        k, x, state_names, u, input_names = read_xk(input_path)
        output_path = resolve_output_path(input_path, args.out, args.format)
        title = args.title or f"Discrete-time state trajectory: {input_path.stem}"

        plot_xk(
            k=k,
            x=x,
            state_names=state_names,
            u=u,
            input_names=input_names,
            output_path=output_path,
            title=title,
            style=args.style,
            include_input=not args.no_input,
            show=args.show,
        )

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("MATLAB-style x(k) plot complete.")
    print(f"  package_dir : {package_dir()}")
    print(f"  sandbox_dir : {sandbox_dir()}")
    print(f"  input       : {input_path}")
    print(f"  output      : {output_path}")
    print(f"  states      : {', '.join(state_names)}")
    if u is not None and input_names:
        print(f"  inputs      : {', '.join(input_names)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
