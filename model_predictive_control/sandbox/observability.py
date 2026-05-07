#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
observability.py

Rawlings/Mayne/Diehl, Model Predictive Control, Section 1.4.5 sandbox.

This standalone script builds observability matrices, checks rank tests, and
logs actual calculations for Lemma 1.4 / equation (1.37) in both forms:

    rank([lambda I - A; C]) = n for all lambda in C

and the equivalent finite check

    rank([lambda I - A; C]) = n for all lambda in eig(A)

The script uses a two-state discrete-time kinematic model so the math is easy
to inspect. It also includes a deliberately unobservable comparison case.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import json
import math

import numpy as np
import matplotlib.pyplot as plt


OUT_DIR = Path("out/observability")
DT = 0.1


def fmt_array(a: np.ndarray, precision: int = 6) -> str:
    return np.array2string(np.asarray(a), precision=precision, suppress_small=False)


def matrix_rank(a: np.ndarray, tol: float = 1e-10) -> int:
    return int(np.linalg.matrix_rank(np.asarray(a, dtype=complex), tol=tol))


def observability_matrix(A: np.ndarray, C: np.ndarray, horizon: int | None = None) -> np.ndarray:
    """Build O_N = [C; C A; ...; C A^{N-1}]."""
    n = A.shape[0]
    N = n if horizon is None else int(horizon)
    blocks = []
    Apow = np.eye(n)
    for _ in range(N):
        blocks.append(C @ Apow)
        Apow = Apow @ A
    return np.vstack(blocks)


def hautus_matrix(A: np.ndarray, C: np.ndarray, lam: complex) -> np.ndarray:
    """Build the observability Hautus matrix [lambda I - A; C]."""
    n = A.shape[0]
    top = lam * np.eye(n, dtype=complex) - A.astype(complex)
    return np.vstack([top, C.astype(complex)])


def nullspace(a: np.ndarray, tol: float = 1e-10) -> np.ndarray:
    """Return an orthonormal basis for the nullspace of a matrix."""
    u, s, vh = np.linalg.svd(np.asarray(a, dtype=float), full_matrices=True)
    rank = int((s > tol).sum())
    return vh[rank:].T.copy()


@dataclass
class CaseResult:
    name: str
    A: np.ndarray
    C: np.ndarray
    O: np.ndarray
    O_rank: int
    O_singular_values: np.ndarray
    eigvals: np.ndarray
    hautus_ranks_eig: list[int]
    hautus_min_rank_grid: int
    is_observable_by_O: bool
    is_observable_by_hautus_eigs: bool
    nullspace_O: np.ndarray
    y_stack: np.ndarray
    x0_true: np.ndarray
    x0_recovered_pinv: np.ndarray
    reconstruction_residual: np.ndarray


def analyze_case(name: str, A: np.ndarray, C: np.ndarray, x0_true: np.ndarray, grid_points: Iterable[complex]) -> CaseResult:
    n = A.shape[0]
    O = observability_matrix(A, C, horizon=n)
    O_rank = matrix_rank(O)
    svals = np.linalg.svd(O, compute_uv=False)
    eigvals = np.linalg.eigvals(A)
    hautus_ranks = [matrix_rank(hautus_matrix(A, C, lam)) for lam in eigvals]
    grid_ranks = [matrix_rank(hautus_matrix(A, C, lam)) for lam in grid_points]
    null_O = nullspace(O)
    y_stack = O @ x0_true
    x0_hat = np.linalg.pinv(O) @ y_stack
    rec_resid = O @ x0_hat - y_stack
    return CaseResult(
        name=name,
        A=A,
        C=C,
        O=O,
        O_rank=O_rank,
        O_singular_values=svals,
        eigvals=eigvals,
        hautus_ranks_eig=hautus_ranks,
        hautus_min_rank_grid=min(grid_ranks),
        is_observable_by_O=(O_rank == n),
        is_observable_by_hautus_eigs=all(r == n for r in hautus_ranks),
        nullspace_O=null_O,
        y_stack=y_stack,
        x0_true=x0_true,
        x0_recovered_pinv=x0_hat,
        reconstruction_residual=rec_resid,
    )


def simulate_outputs(A: np.ndarray, C: np.ndarray, x0: np.ndarray, steps: int) -> tuple[np.ndarray, np.ndarray]:
    xs = np.zeros((steps + 1, A.shape[0]))
    ys = np.zeros((steps + 1, C.shape[0]))
    xs[0] = x0
    ys[0] = C @ x0
    for k in range(steps):
        xs[k + 1] = A @ xs[k]
        ys[k + 1] = C @ xs[k + 1]
    return xs, ys


def write_csv(path: Path, headers: list[str], rows: list[list[float | int | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(",".join(headers) + "\n")
        for row in rows:
            out = []
            for val in row:
                if isinstance(val, float):
                    out.append(f"{val:.12g}")
                else:
                    out.append(str(val))
            f.write(",".join(out) + "\n")


def plot_observability_heatmaps(cases: list[CaseResult], out_dir: Path) -> Path:
    fig, axes = plt.subplots(1, len(cases), figsize=(12, 4.8))
    if len(cases) == 1:
        axes = [axes]
    for ax, case in zip(axes, cases):
        im = ax.imshow(case.O, aspect="auto")
        ax.set_title(f"{case.name}\nO rank = {case.O_rank}")
        ax.set_xlabel("state column")
        ax.set_ylabel("measurement block row")
        for i in range(case.O.shape[0]):
            for j in range(case.O.shape[1]):
                ax.text(j, i, f"{case.O[i, j]:.2g}", ha="center", va="center")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle("Observability matrix O = [C; CA; ...; CA^(n-1)]")
    fig.tight_layout()
    path = out_dir / "observability_matrix_heatmap.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def plot_rank_growth(cases: list[CaseResult], out_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for case in cases:
        n = case.A.shape[0]
        horizons = np.arange(1, 8)
        ranks = [matrix_rank(observability_matrix(case.A, case.C, horizon=int(N))) for N in horizons]
        ax.step(horizons, ranks, where="post", label=f"{case.name}")
    ax.axhline(cases[0].A.shape[0], linestyle="--", label="full state dimension n")
    ax.set_title("Rank growth as more output samples are stacked")
    ax.set_xlabel("number of measurements stacked N")
    ax.set_ylabel("rank of O_N")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    fig.tight_layout()
    path = out_dir / "observability_rank_growth.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def plot_hautus_grid(cases: list[CaseResult], out_dir: Path) -> Path:
    re = np.linspace(-1.2, 1.4, 90)
    im = np.linspace(-1.0, 1.0, 70)
    fig, axes = plt.subplots(1, len(cases), figsize=(13, 5.2))
    if len(cases) == 1:
        axes = [axes]
    for ax, case in zip(axes, cases):
        ranks = np.zeros((len(im), len(re)))
        for ii, b in enumerate(im):
            for jj, a in enumerate(re):
                ranks[ii, jj] = matrix_rank(hautus_matrix(case.A, case.C, a + 1j * b))
        img = ax.imshow(ranks, extent=[re.min(), re.max(), im.min(), im.max()], origin="lower", aspect="auto")
        eigs = case.eigvals
        ax.scatter(np.real(eigs), np.imag(eigs), marker="x", s=70, label="eig(A)")
        ax.set_title(f"{case.name}\nrank([lambda I-A; C]) over complex grid")
        ax.set_xlabel("Re(lambda)")
        ax.set_ylabel("Im(lambda)")
        ax.grid(True, alpha=0.2)
        ax.legend(loc="best")
        fig.colorbar(img, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    path = out_dir / "hautus_rank_grid.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def plot_output_distinguishing(A: np.ndarray, Cobs: np.ndarray, Cunobs: np.ndarray, out_dir: Path) -> Path:
    steps = 20
    x0_a = np.array([2.5, -0.3])
    x0_b = np.array([3.2, -0.3])  # same velocity, different position
    _, y_obs_a = simulate_outputs(A, Cobs, x0_a, steps)
    _, y_obs_b = simulate_outputs(A, Cobs, x0_b, steps)
    _, y_unobs_a = simulate_outputs(A, Cunobs, x0_a, steps)
    _, y_unobs_b = simulate_outputs(A, Cunobs, x0_b, steps)
    t = np.arange(steps + 1) * DT

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(t, y_obs_a[:, 0], label="observable C=[1 0], x0 A")
    ax.plot(t, y_obs_b[:, 0], linestyle="--", label="observable C=[1 0], x0 B")
    ax.plot(t, y_unobs_a[:, 0], label="unobservable C=[0 1], x0 A")
    ax.plot(t, y_unobs_b[:, 0], linestyle="--", label="unobservable C=[0 1], x0 B")
    ax.set_title("Can two different initial states be distinguished by outputs?")
    ax.set_xlabel("time")
    ax.set_ylabel("measured output y")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    fig.tight_layout()
    path = out_dir / "output_distinguishing_demo.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def plot_singular_values(cases: list[CaseResult], out_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5))
    for case in cases:
        ax.semilogy(np.arange(1, len(case.O_singular_values) + 1), case.O_singular_values, marker="o", label=case.name)
    ax.set_title("Singular values of observability matrix")
    ax.set_xlabel("singular value index")
    ax.set_ylabel("singular value")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="best")
    fig.tight_layout()
    path = out_dir / "observability_singular_values.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def main() -> int:
    out_dir = OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    A = np.array([[1.0, DT], [0.0, 1.0]])
    C_position = np.array([[1.0, 0.0]])
    C_velocity = np.array([[0.0, 1.0]])
    x0_true = np.array([2.5, -0.4])

    # A modest complex grid demonstrates the all-lambda Hautus form numerically.
    grid_points = [a + 1j * b for a in np.linspace(-1.5, 1.5, 31) for b in np.linspace(-1.0, 1.0, 21)]

    cases = [
        analyze_case("observable: measure position", A, C_position, x0_true, grid_points),
        analyze_case("unobservable: measure velocity only", A, C_velocity, x0_true, grid_points),
    ]

    plot_paths = {
        "observability_matrix_heatmap": plot_observability_heatmaps(cases, out_dir),
        "rank_growth": plot_rank_growth(cases, out_dir),
        "hautus_rank_grid": plot_hautus_grid(cases, out_dir),
        "output_distinguishing_demo": plot_output_distinguishing(A, C_position, C_velocity, out_dir),
        "singular_values": plot_singular_values(cases, out_dir),
    }

    rows = []
    for case in cases:
        for N in range(1, 8):
            ON = observability_matrix(case.A, case.C, horizon=N)
            rows.append([case.name, N, ON.shape[0], ON.shape[1], matrix_rank(ON)])
    write_csv(out_dir / "observability_rank_growth.csv", ["case", "N_measurements", "rows", "cols", "rank"], rows)

    summary = {
        "section": "Rawlings/Mayne/Diehl 1.4.5 Observability",
        "A": A.tolist(),
        "dt": DT,
        "cases": [],
        "plot_files": {k: str(v) for k, v in plot_paths.items()},
    }
    for case in cases:
        summary["cases"].append({
            "name": case.name,
            "C": case.C.tolist(),
            "O": case.O.tolist(),
            "O_rank": case.O_rank,
            "n": int(case.A.shape[0]),
            "observable_by_O_rank": case.is_observable_by_O,
            "eig_A": [[float(np.real(v)), float(np.imag(v))] for v in case.eigvals],
            "hautus_ranks_at_eig_A": case.hautus_ranks_eig,
            "observable_by_hautus_eigenvalue_form": case.is_observable_by_hautus_eigs,
            "hautus_min_rank_on_demonstration_grid": case.hautus_min_rank_grid,
            "nullspace_O": case.nullspace_O.tolist(),
            "x0_true": case.x0_true.tolist(),
            "stacked_outputs_y": case.y_stack.tolist(),
            "x0_recovered_by_pseudoinverse": case.x0_recovered_pinv.tolist(),
            "reconstruction_residual": case.reconstruction_residual.tolist(),
        })

    with (out_dir / "observability_results.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")

    log = []
    add = log.append
    add("Observability Calculation Log")
    add("Rawlings/Mayne/Diehl Section 1.4.5 sandbox")
    add("")
    add("Linear zero-input model used for observability")
    add("  x(k+1) = A x(k)")
    add("  y(k)   = C x(k)")
    add("  Inputs are irrelevant for LTI observability, so they are set to zero.")
    add("")
    add("Textbook construction")
    add("  Stack n measurements:")
    add("    [y(0); y(1); ...; y(n-1)] = O x(0)")
    add("  Observability matrix:")
    add("    O = [C; C A; ...; C A^(n-1)]")
    add("  Observable iff rank(O) = n")
    add("")
    add("Lemma 1.4 / equation 1.37, form 1")
    add("  Observable iff rank([lambda I - A; C]) = n for all lambda in complex numbers C.")
    add("")
    add("Lemma 1.4 / equation 1.37, form 2")
    add("  Since lambda I - A already has full rank when lambda is not an eigenvalue of A,")
    add("  it is enough to check rank([lambda I - A; C]) = n for all lambda in eig(A).")
    add("")
    add("Shared A matrix")
    add(f"A = {fmt_array(A)}")
    add(f"eig(A) = {fmt_array(np.linalg.eigvals(A))}")
    add("")

    for case in cases:
        add("-" * 78)
        add(f"Case: {case.name}")
        add(f"C = {fmt_array(case.C)}")
        add(f"n = {case.A.shape[0]}, p = {case.C.shape[0]}")
        add("")
        add("Observability matrix calculation")
        for j in range(case.A.shape[0]):
            add(f"C A^{j} = {fmt_array(case.C @ np.linalg.matrix_power(case.A, j))}")
        add(f"O = {fmt_array(case.O)}")
        add(f"singular values of O = {fmt_array(case.O_singular_values)}")
        add(f"rank(O) = {case.O_rank}")
        add(f"rank(O) == n ? {case.is_observable_by_O}")
        add("")
        add("Initial-state reconstruction test from stacked outputs")
        add(f"x0_true = {fmt_array(case.x0_true)}")
        add(f"stacked y = O x0_true = {fmt_array(case.y_stack)}")
        add(f"pinv(O) stacked_y = {fmt_array(case.x0_recovered_pinv)}")
        add(f"O pinv(O) stacked_y - stacked_y = {fmt_array(case.reconstruction_residual)}")
        if case.nullspace_O.size:
            add(f"nullspace(O) basis = {fmt_array(case.nullspace_O)}")
            add("Any nonzero vector in nullspace(O) is an initial-state direction hidden from the outputs.")
        else:
            add("nullspace(O) is empty: no nonzero initial-state direction is hidden from n outputs.")
        add("")
        add("Hautus rank checks at eigenvalues of A")
        for lam, rank in zip(case.eigvals, case.hautus_ranks_eig):
            Hlam = hautus_matrix(case.A, case.C, lam)
            add(f"lambda = {lam:.12g}")
            add(f"[lambda I - A; C] = {fmt_array(Hlam)}")
            add(f"rank([lambda I - A; C]) = {rank}")
        add(f"All eigenvalue Hautus ranks equal n? {case.is_observable_by_hautus_eigs}")
        add("")
        add("All-lambda Hautus form demonstration")
        add(f"Minimum rank over {len(grid_points)} sampled complex lambda values = {case.hautus_min_rank_grid}")
        if case.name.startswith("observable"):
            add("For this 2-state position-measured double integrator, the rows [1, 0] and [lambda-1, -dt]")
            add("are linearly independent for any lambda because dt != 0. This demonstrates the all-lambda form.")
        else:
            add("At lambda = 1, the first column of [lambda I - A; C] vanishes, so rank drops below n.")
        add("")

    add("Engineering interpretation")
    add("  Observability asks whether output history contains enough information to recover the state.")
    add("  For A = [[1, dt], [0, 1]], measuring position is observable because two position samples reveal velocity.")
    add("  Measuring velocity only is not observable because the initial position never appears in y(k).")
    add("  In state estimation and MPC, unobservable state components cannot be reconstructed from sensors no matter how clever the estimator is.")
    add("")
    add("Generated files")
    for key, path in plot_paths.items():
        add(f"  {key}: {path}")
    add(f"  results_json: {out_dir / 'observability_results.json'}")
    add(f"  rank_growth_csv: {out_dir / 'observability_rank_growth.csv'}")

    log_path = out_dir / "observability_calculation_log.txt"
    log_path.write_text("\n".join(log) + "\n", encoding="utf-8")

    print("Observability sandbox complete.")
    print(f"Script: {Path(__file__).resolve()}")
    print(f"Output directory: {out_dir.resolve()}")
    print(f"Calculation log: {log_path.resolve()}")
    for key, path in plot_paths.items():
        print(f"{key}: {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
