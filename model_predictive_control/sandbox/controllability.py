#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
controllability_sandbox.py

Sandbox script for studying controllability in Rawlings, Mayne, and Diehl,
Model Predictive Control: Theory, Computation, and Design, Section 1.3.5.

What this script does
---------------------
For each linear discrete-time system

    x(k + 1) = A x(k) + B u(k)

this script logs:

1. the controllability matrix

       C = [ B  A B  A^2 B  ...  A^(n-1) B ]

2. rank(C), singular values, and the ordinary controllability conclusion.

3. Lemma 1.2 / Hautus test in the form

       rank([lambda I - A   B]) = n for all lambda in C.

   Computationally, we cannot loop over every complex lambda. The script logs
   the theoretical reduction used by the text: if lambda is not an eigenvalue
   of A, the first n columns lambda I - A are already full rank. Therefore,
   the only lambdas that must be checked are eigenvalues of A.

4. Lemma 1.2 equivalent eigenvalue-only test

       rank([lambda I - A   B]) = n for all lambda in eig(A).

Outputs
-------
By default, outputs are written to a simple directory named:

    controllability/

The script writes:

    controllability_results.json
    controllability_summary.csv
    controllability_report.md

Run examples
------------
From the folder containing this file:

    python controllability_sandbox.py

Run a custom JSON input file:

    python controllability_sandbox.py --input in/my_controllability_case.json

Write somewhere else:

    python controllability_sandbox.py --out controllability

Custom JSON input format
------------------------
The input file may contain either one case:

    {
      "title": "My system",
      "A": [[1.0, 0.1], [0.0, 1.0]],
      "B": [[0.005], [0.1]],
      "lambda_probe_points": [0, 1, {"real": 0.5, "imag": 0.25}]
    }

or many cases:

    {
      "cases": [
        {"title": "case 1", "A": [[...]], "B": [[...]]},
        {"title": "case 2", "A": [[...]], "B": [[...]]}
      ]
    }
"""

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


DEFAULT_RANK_TOL = 1.0e-9


@dataclass(frozen=True)
class ControllabilityCase:
    """One state-space pair (A, B) to test."""

    title: str
    A: np.ndarray
    B: np.ndarray
    lambda_probe_points: list[complex]


# ---------------------------------------------------------------------------
# Small conversion and validation helpers
# ---------------------------------------------------------------------------

def _as_matrix(value: Any, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=float)
    if arr.ndim != 2:
        raise ValueError(f"{name} must be a 2-D matrix; got shape {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains non-finite values")
    return arr


def _as_square_matrix(value: Any, name: str) -> np.ndarray:
    arr = _as_matrix(value, name)
    if arr.shape[0] != arr.shape[1]:
        raise ValueError(f"{name} must be square; got shape {arr.shape}")
    return arr


def _complex_from_json(value: Any) -> complex:
    if isinstance(value, dict):
        return complex(float(value.get("real", 0.0)), float(value.get("imag", 0.0)))
    if isinstance(value, (int, float)):
        return complex(float(value), 0.0)
    if isinstance(value, str):
        return complex(value.replace("i", "j"))
    raise ValueError(f"Cannot parse complex value from {value!r}")


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return _to_jsonable(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag), "text": _format_complex(value)}
    if isinstance(value, list):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, tuple):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, Path):
        return str(value)
    return value


def _format_float(x: float, digits: int = 10) -> str:
    if abs(x) < 10 ** (-(digits - 2)):
        x = 0.0
    return f"{x:.{digits}g}"


def _format_complex(z: complex, digits: int = 10) -> str:
    real = 0.0 if abs(z.real) < 10 ** (-(digits - 2)) else z.real
    imag = 0.0 if abs(z.imag) < 10 ** (-(digits - 2)) else z.imag
    if imag == 0.0:
        return _format_float(real, digits)
    if real == 0.0:
        return f"{_format_float(imag, digits)}j"
    sign = "+" if imag >= 0.0 else "-"
    return f"{_format_float(real, digits)} {sign} {_format_float(abs(imag), digits)}j"


# ---------------------------------------------------------------------------
# Controllability and Hautus calculations
# ---------------------------------------------------------------------------

def matrix_rank(M: np.ndarray, tol: float = DEFAULT_RANK_TOL) -> int:
    """Rank helper with explicit tolerance so results are reproducible."""

    return int(np.linalg.matrix_rank(M, tol=tol))


def controllability_matrix(A: np.ndarray, B: np.ndarray) -> tuple[np.ndarray, list[np.ndarray], list[np.ndarray]]:
    """Build C = [B, A B, ..., A^(n-1) B]."""

    n = A.shape[0]
    powers: list[np.ndarray] = []
    blocks: list[np.ndarray] = []
    current_power = np.eye(n)
    for k in range(n):
        powers.append(current_power.copy())
        blocks.append(current_power @ B)
        current_power = current_power @ A
    C = np.hstack(blocks)
    return C, powers, blocks


def hautus_matrix(A: np.ndarray, B: np.ndarray, lam: complex) -> np.ndarray:
    """Build the Hautus matrix [lambda I - A, B]."""

    n = A.shape[0]
    return np.hstack([lam * np.eye(n, dtype=complex) - A.astype(complex), B.astype(complex)])


def hautus_test_for_lambdas(A: np.ndarray, B: np.ndarray, lambdas: list[complex], tol: float) -> list[dict[str, Any]]:
    """Evaluate rank([lambda I - A, B]) for a finite list of lambdas."""

    n = A.shape[0]
    rows: list[dict[str, Any]] = []
    for lam in lambdas:
        H = hautus_matrix(A, B, lam)
        svals = np.linalg.svd(H, compute_uv=False)
        rank = matrix_rank(H, tol=tol)
        rows.append(
            {
                "lambda": lam,
                "hautus_matrix": H,
                "rank": rank,
                "required_rank": n,
                "passes": bool(rank == n),
                "singular_values": svals,
            }
        )
    return rows


def unique_complex_values(values: list[complex], tol: float = 1e-8) -> list[complex]:
    """Return complex values with near-duplicates removed while preserving order."""

    out: list[complex] = []
    for z in values:
        if not any(abs(z - w) <= tol for w in out):
            out.append(z)
    return out


def analyze_case(case: ControllabilityCase, tol: float = DEFAULT_RANK_TOL) -> dict[str, Any]:
    """Run all controllability tests for one case."""

    A = case.A
    B = case.B
    if A.shape[0] != B.shape[0]:
        raise ValueError(f"A and B row mismatch for {case.title!r}: A{A.shape}, B{B.shape}")

    n = A.shape[0]
    m = B.shape[1]
    Cmat, powers, blocks = controllability_matrix(A, B)
    c_svals = np.linalg.svd(Cmat, compute_uv=False)
    c_rank = matrix_rank(Cmat, tol=tol)
    c_condition = float(c_svals[0] / c_svals[-1]) if c_svals.size and c_svals[-1] > 0 else math.inf

    eigvals = [complex(v) for v in np.linalg.eigvals(A)]
    eigvals_unique = unique_complex_values(eigvals)

    # This is the finite practical version of the equation 1.17 check. The
    # rigorous finite check is the eigenvalue-only test below. Probe points are
    # extra diagnostic points to make the "for all lambda" statement concrete.
    probe_lambdas = unique_complex_values([*eigvals_unique, *case.lambda_probe_points])
    full_lambda_probe_rows = hautus_test_for_lambdas(A, B, probe_lambdas, tol)
    eig_only_rows = hautus_test_for_lambdas(A, B, eigvals_unique, tol)

    controllable_by_C = bool(c_rank == n)
    controllable_by_eig_hautus = bool(all(row["passes"] for row in eig_only_rows))
    controllable_by_probe_hautus = bool(all(row["passes"] for row in full_lambda_probe_rows))

    return {
        "title": case.title,
        "n_states": n,
        "m_inputs": m,
        "rank_tolerance": tol,
        "A": A,
        "B": B,
        "A_powers": {f"A^{k}": powers[k] for k in range(len(powers))},
        "controllability_blocks": {f"A^{k}B": blocks[k] for k in range(len(blocks))},
        "controllability_matrix_definition": "C = [B, AB, A^2B, ..., A^(n-1)B]",
        "controllability_matrix": Cmat,
        "controllability_matrix_shape": Cmat.shape,
        "controllability_rank": c_rank,
        "controllability_required_rank": n,
        "controllability_singular_values": c_svals,
        "controllability_condition_number": c_condition,
        "controllable_by_controllability_matrix_rank": controllable_by_C,
        "eigenvalues_of_A": eigvals,
        "unique_eigenvalues_checked": eigvals_unique,
        "lemma_1_2_equation_1_17": {
            "statement": "rank([lambda I - A, B]) = n for all lambda in C",
            "computational_note": (
                "The full statement quantifies over infinitely many complex lambdas. "
                "For an LTI finite-dimensional system, lambdas that are not eigenvalues "
                "of A automatically pass because lambda I - A is nonsingular. The script "
                "therefore logs extra probe points and uses the eigenvalue-only test as "
                "the rigorous finite check."
            ),
            "probe_lambdas_checked": probe_lambdas,
            "probe_results": full_lambda_probe_rows,
            "passes_all_probe_lambdas": controllable_by_probe_hautus,
        },
        "lemma_1_2_eigenvalue_equivalent_test": {
            "statement": "rank([lambda I - A, B]) = n for all lambda in eig(A)",
            "results": eig_only_rows,
            "passes": controllable_by_eig_hautus,
        },
        "agreement_check": {
            "rank_C_equals_eigenvalue_Hautus": bool(controllable_by_C == controllable_by_eig_hautus),
            "controllability_conclusion": "controllable" if controllable_by_C else "not controllable",
        },
    }


# ---------------------------------------------------------------------------
# Input and default cases
# ---------------------------------------------------------------------------

def default_cases() -> list[ControllabilityCase]:
    """Built-in cases used when no input file is provided."""

    rawlings_A = np.array([[4.0 / 3.0, -2.0 / 3.0], [1.0, 0.0]], dtype=float)
    rawlings_B = np.array([[1.0], [0.0]], dtype=float)

    dt = 0.1
    double_integrator_A = np.array([[1.0, dt], [0.0, 1.0]], dtype=float)
    double_integrator_B = np.array([[0.5 * dt * dt], [dt]], dtype=float)

    uncontrollable_A_I = np.eye(2)
    uncontrollable_B_zero = np.zeros((2, 1))

    partial_A = np.array([[1.2, 0.0], [0.0, 0.8]], dtype=float)
    partial_B = np.array([[1.0], [0.0]], dtype=float)

    common_probes = [0.0 + 0.0j, 0.5 + 0.25j, 1.0 + 0.0j, 1.5 + 0.0j]

    return [
        ControllabilityCase(
            title="Rawlings page 21 LQ example system",
            A=rawlings_A,
            B=rawlings_B,
            lambda_probe_points=common_probes,
        ),
        ControllabilityCase(
            title="Discrete double integrator with dt=0.1",
            A=double_integrator_A,
            B=double_integrator_B,
            lambda_probe_points=common_probes,
        ),
        ControllabilityCase(
            title="Uncontrollable sanity check: A = I, B = 0",
            A=uncontrollable_A_I,
            B=uncontrollable_B_zero,
            lambda_probe_points=common_probes,
        ),
        ControllabilityCase(
            title="Partly uncontrollable mode sanity check",
            A=partial_A,
            B=partial_B,
            lambda_probe_points=common_probes,
        ),
    ]


def load_cases_from_json(path: Path) -> list[ControllabilityCase]:
    with path.expanduser().resolve().open("r", encoding="utf-8") as f:
        data = json.load(f)

    raw_cases = data.get("cases") if isinstance(data, dict) and "cases" in data else [data]
    if not isinstance(raw_cases, list):
        raise ValueError("Input JSON 'cases' must be a list")

    cases: list[ControllabilityCase] = []
    for i, raw in enumerate(raw_cases):
        if not isinstance(raw, dict):
            raise ValueError(f"Case {i} must be an object")
        title = str(raw.get("title", f"case_{i + 1}"))
        A = _as_square_matrix(raw.get("A"), f"cases[{i}].A")
        B = _as_matrix(raw.get("B"), f"cases[{i}].B")
        probes = [_complex_from_json(v) for v in raw.get("lambda_probe_points", [])]
        cases.append(ControllabilityCase(title=title, A=A, B=B, lambda_probe_points=probes))
    return cases


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_json(results: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(_to_jsonable(results), f, indent=2)
        f.write("\n")


def write_summary_csv(results: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "title",
                "n_states",
                "m_inputs",
                "rank_C",
                "required_rank",
                "controllable_by_C",
                "passes_Hautus_eigenvalue_test",
                "conclusion",
                "eigenvalues_A",
                "singular_values_C",
                "condition_number_C",
            ]
        )
        for r in results:
            writer.writerow(
                [
                    r["title"],
                    r["n_states"],
                    r["m_inputs"],
                    r["controllability_rank"],
                    r["controllability_required_rank"],
                    r["controllable_by_controllability_matrix_rank"],
                    r["lemma_1_2_eigenvalue_equivalent_test"]["passes"],
                    r["agreement_check"]["controllability_conclusion"],
                    "; ".join(_format_complex(z) for z in r["eigenvalues_of_A"]),
                    "; ".join(_format_float(float(s)) for s in r["controllability_singular_values"]),
                    _format_float(float(r["controllability_condition_number"])) if math.isfinite(float(r["controllability_condition_number"])) else "inf",
                ]
            )


def _markdown_matrix(M: np.ndarray, digits: int = 8) -> str:
    arr = np.asarray(M)
    lines = []
    for row in arr:
        items = []
        for v in row:
            if isinstance(v, complex) or np.iscomplexobj(v):
                items.append(_format_complex(complex(v), digits))
            else:
                items.append(_format_float(float(v), digits))
        lines.append("[" + ", ".join(items) + "]")
    return "\n".join(lines)


def write_report(results: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write("# Controllability Sandbox Report\n\n")
        f.write("This report was generated by `controllability_sandbox.py`.\n\n")
        f.write("The output directory is intentionally named `controllability`.\n\n")
        f.write("## Theory checks implemented\n\n")
        f.write("- Controllability matrix: `C = [B, AB, ..., A^(n-1)B]`.\n")
        f.write("- Rank test: controllable if `rank(C) = n`.\n")
        f.write("- Hautus test, equation 1.17: `rank([lambda I - A, B]) = n` for all complex `lambda`.\n")
        f.write("- Eigenvalue-only Hautus test: it is sufficient to check `lambda in eig(A)`.\n\n")

        for r in results:
            f.write(f"## {r['title']}\n\n")
            f.write(f"- n states: `{r['n_states']}`\n")
            f.write(f"- m inputs: `{r['m_inputs']}`\n")
            f.write(f"- rank tolerance: `{r['rank_tolerance']}`\n")
            f.write(f"- eigenvalues of A: {', '.join(_format_complex(z) for z in r['eigenvalues_of_A'])}\n")
            f.write(f"- rank(C): `{r['controllability_rank']}` / required `{r['controllability_required_rank']}`\n")
            f.write(f"- controllability conclusion: **{r['agreement_check']['controllability_conclusion']}**\n")
            f.write(f"- Hautus eigenvalue test passes: `{r['lemma_1_2_eigenvalue_equivalent_test']['passes']}`\n\n")

            f.write("### A\n\n```text\n")
            f.write(_markdown_matrix(r["A"]))
            f.write("\n```\n\n")

            f.write("### B\n\n```text\n")
            f.write(_markdown_matrix(r["B"]))
            f.write("\n```\n\n")

            f.write("### Controllability matrix C\n\n```text\n")
            f.write(_markdown_matrix(r["controllability_matrix"]))
            f.write("\n```\n\n")

            f.write("### Controllability blocks\n\n")
            for name, block in r["controllability_blocks"].items():
                f.write(f"#### {name}\n\n```text\n")
                f.write(_markdown_matrix(block))
                f.write("\n```\n\n")

            f.write("### Lemma 1.2 eigenvalue-only Hautus test\n\n")
            for row in r["lemma_1_2_eigenvalue_equivalent_test"]["results"]:
                f.write(f"#### lambda = {_format_complex(row['lambda'])}\n\n")
                f.write(f"rank = `{row['rank']}` / required `{row['required_rank']}`; passes = `{row['passes']}`\n\n")
                f.write("H(lambda) = [lambda I - A, B]\n\n```text\n")
                f.write(_markdown_matrix(row["hautus_matrix"]))
                f.write("\n```\n\n")

            f.write("### Equation 1.17 finite probe log\n\n")
            f.write(r["lemma_1_2_equation_1_17"]["computational_note"] + "\n\n")
            for row in r["lemma_1_2_equation_1_17"]["probe_results"]:
                f.write(f"- lambda = `{_format_complex(row['lambda'])}`: rank `{row['rank']}` / `{row['required_rank']}`, passes `{row['passes']}`\n")
            f.write("\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="controllability_sandbox",
        description="Build controllability matrices and run Rawlings Lemma 1.2 Hautus tests.",
    )
    parser.add_argument("--input", default=None, help="Optional JSON file containing one case or a list of cases.")
    parser.add_argument("--out", default="out/controllability", help="Output directory. Default: controllability")
    parser.add_argument("--tol", type=float, default=DEFAULT_RANK_TOL, help="Rank tolerance. Default: 1e-9")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.input:
        cases = load_cases_from_json(Path(args.input))
    else:
        cases = default_cases()

    results = [analyze_case(case, tol=float(args.tol)) for case in cases]

    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "script": Path(__file__).name,
        "output_directory": out_dir,
        "rank_tolerance": float(args.tol),
        "cases_analyzed": len(results),
        "results": results,
    }

    json_path = out_dir / "controllability_results.json"
    csv_path = out_dir / "controllability_summary.csv"
    report_path = out_dir / "controllability_report.md"

    write_json(payload, json_path)
    write_summary_csv(results, csv_path)
    write_report(results, report_path)

    print("Controllability sandbox complete.")
    print(f"Output directory : {out_dir}")
    print(f"JSON log         : {json_path}")
    print(f"CSV summary      : {csv_path}")
    print(f"Markdown report  : {report_path}")
    print("")
    for r in results:
        print(
            f"- {r['title']}: rank(C)={r['controllability_rank']}/{r['controllability_required_rank']}, "
            f"Hautus eig test={r['lemma_1_2_eigenvalue_equivalent_test']['passes']}, "
            f"conclusion={r['agreement_check']['controllability_conclusion']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
