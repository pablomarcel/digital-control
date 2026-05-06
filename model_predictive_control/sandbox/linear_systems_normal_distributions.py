#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
linear_systems_normal_distributions.py

Sandbox for Rawlings/Mayne/Diehl, Section 1.4.1:
Linear Systems and Normal Distributions.

The point of this script is not to build a full Kalman filter yet. The point is
just to make equations (1.20) through (1.25) concrete with matrices that can be
printed, saved, and inspected.

Implemented checks
------------------
1. Eq. (1.20): joint distribution of independent normal random vectors.
2. Eq. (1.21): linear transformation of a normal random vector.
3. Eq. (1.22): conditional distribution of one block of a joint normal.
4. Eq. (1.23): conditional joint distribution when x|z is normal and y is
   independent of x and z.
5. Eq. (1.24): conditional linear transformation of x|z.
6. Eq. (1.25): conditional distribution of one block of a joint conditional
   normal distribution.

Default output directory
------------------------
out/normal_distributions

Run examples
------------
python linear_systems_normal_distributions.py
python linear_systems_normal_distributions.py --out out/normal_distributions --pretty
python linear_systems_normal_distributions.py --samples 50000 --seed 7
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import argparse
import csv
import json

import numpy as np


@dataclass(frozen=True)
class NormalDistribution:
    """Mean and covariance representation of a multivariate normal."""

    mean: np.ndarray
    covariance: np.ndarray

    @property
    def dimension(self) -> int:
        return int(self.mean.size)


def as_vector(value: Any, name: str) -> np.ndarray:
    """Convert a value to a finite one-dimensional float vector."""

    arr = np.asarray(value, dtype=float)
    if arr.ndim != 1:
        raise ValueError(f"{name} must be a 1-D vector; got shape {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains non-finite values")
    return arr


def as_matrix(value: Any, name: str) -> np.ndarray:
    """Convert a value to a finite two-dimensional float matrix."""

    arr = np.asarray(value, dtype=float)
    if arr.ndim != 2:
        raise ValueError(f"{name} must be a 2-D matrix; got shape {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains non-finite values")
    return arr


def require_symmetric_square(P: np.ndarray, name: str, *, atol: float = 1e-10) -> np.ndarray:
    """Validate that a covariance matrix is square and symmetric."""

    P = as_matrix(P, name)
    if P.shape[0] != P.shape[1]:
        raise ValueError(f"{name} must be square; got shape {P.shape}")
    if not np.allclose(P, P.T, atol=atol):
        raise ValueError(f"{name} must be symmetric")
    return P


def block_diag(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Small NumPy-only block diagonal helper."""

    A = as_matrix(A, "A")
    B = as_matrix(B, "B")
    out = np.zeros((A.shape[0] + B.shape[0], A.shape[1] + B.shape[1]))
    out[: A.shape[0], : A.shape[1]] = A
    out[A.shape[0] :, A.shape[1] :] = B
    return out


def joint_independent_normals(
    mx: np.ndarray,
    Px: np.ndarray,
    my: np.ndarray,
    Py: np.ndarray,
) -> NormalDistribution:
    """Equations (1.20) and (1.23): stack independent normal variables.

    If x is normal with mean mx and covariance Px, and y is independent and
    normal with mean my and covariance Py, then [x; y] is normal with stacked
    mean [mx; my] and block-diagonal covariance diag(Px, Py).
    """

    mx = as_vector(mx, "mx")
    my = as_vector(my, "my")
    Px = require_symmetric_square(Px, "Px")
    Py = require_symmetric_square(Py, "Py")
    if Px.shape != (mx.size, mx.size):
        raise ValueError(f"Px shape {Px.shape} is inconsistent with mx length {mx.size}")
    if Py.shape != (my.size, my.size):
        raise ValueError(f"Py shape {Py.shape} is inconsistent with my length {my.size}")
    return NormalDistribution(mean=np.concatenate([mx, my]), covariance=block_diag(Px, Py))


def linear_transform_normal(m: np.ndarray, P: np.ndarray, A: np.ndarray) -> NormalDistribution:
    """Equations (1.21) and (1.24): transform x ~ N(m, P) by y = A x."""

    m = as_vector(m, "m")
    P = require_symmetric_square(P, "P")
    A = as_matrix(A, "A")
    if P.shape != (m.size, m.size):
        raise ValueError(f"P shape {P.shape} is inconsistent with m length {m.size}")
    if A.shape[1] != m.size:
        raise ValueError(f"A has {A.shape[1]} columns but m has length {m.size}")
    return NormalDistribution(mean=A @ m, covariance=A @ P @ A.T)


def conditional_joint_normal(
    mx: np.ndarray,
    Px: np.ndarray,
    my: np.ndarray,
    Py: np.ndarray,
    Pxy: np.ndarray,
    y_observed: np.ndarray,
) -> NormalDistribution:
    """Equations (1.22) and (1.25): compute p(x | y) for a joint normal.

    Given

        [x] ~ N( [mx], [Px   Pxy] )
        [y]      [my]  [Pyx  Py ]

    the conditional distribution p(x | y) is normal with

        m = mx + Pxy inv(Py) (y - my)
        P = Px - Pxy inv(Py) Pyx

    This uses solve(Py, rhs) rather than forming inv(Py) explicitly.
    """

    mx = as_vector(mx, "mx")
    my = as_vector(my, "my")
    y_observed = as_vector(y_observed, "y_observed")
    Px = require_symmetric_square(Px, "Px")
    Py = require_symmetric_square(Py, "Py")
    Pxy = as_matrix(Pxy, "Pxy")
    if Px.shape != (mx.size, mx.size):
        raise ValueError(f"Px shape {Px.shape} is inconsistent with mx length {mx.size}")
    if Py.shape != (my.size, my.size):
        raise ValueError(f"Py shape {Py.shape} is inconsistent with my length {my.size}")
    if Pxy.shape != (mx.size, my.size):
        raise ValueError(f"Pxy must have shape {(mx.size, my.size)}; got {Pxy.shape}")
    if y_observed.size != my.size:
        raise ValueError(f"y_observed length {y_observed.size} is inconsistent with my length {my.size}")

    innovation = y_observed - my
    gain_like = np.linalg.solve(Py, innovation)
    conditional_mean = mx + Pxy @ gain_like

    # Pxy inv(Py) Pyx, written using solve for numerical hygiene.
    conditional_covariance = Px - Pxy @ np.linalg.solve(Py, Pxy.T)
    conditional_covariance = 0.5 * (conditional_covariance + conditional_covariance.T)
    return NormalDistribution(mean=conditional_mean, covariance=conditional_covariance)


def joint_from_blocks(mx: np.ndarray, Px: np.ndarray, my: np.ndarray, Py: np.ndarray, Pxy: np.ndarray) -> NormalDistribution:
    """Build a joint normal from partitioned covariance blocks."""

    mx = as_vector(mx, "mx")
    my = as_vector(my, "my")
    Px = require_symmetric_square(Px, "Px")
    Py = require_symmetric_square(Py, "Py")
    Pxy = as_matrix(Pxy, "Pxy")
    top = np.hstack([Px, Pxy])
    bottom = np.hstack([Pxy.T, Py])
    return NormalDistribution(mean=np.concatenate([mx, my]), covariance=np.vstack([top, bottom]))


def covariance_eigenvalues(P: np.ndarray) -> np.ndarray:
    """Return sorted real eigenvalues of a symmetric covariance matrix."""

    return np.sort(np.linalg.eigvalsh(require_symmetric_square(P, "P")))


def sample_stats(samples: np.ndarray) -> NormalDistribution:
    """Return sample mean and covariance for Monte Carlo sanity checks."""

    samples = np.asarray(samples, dtype=float)
    return NormalDistribution(mean=np.mean(samples, axis=0), covariance=np.cov(samples, rowvar=False, bias=False))


def to_jsonable(value: Any) -> Any:
    """Convert NumPy values to JSON-friendly Python values."""

    if isinstance(value, NormalDistribution):
        return {"mean": to_jsonable(value.mean), "covariance": to_jsonable(value.covariance)}
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    return value


def write_json(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(to_jsonable(data), f, indent=2)
        f.write("\n")


def write_summary_csv(results: dict[str, Any], path: Path) -> None:
    """Write a compact CSV with equation labels, means, and covariance diagonals."""

    path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    for label, item in results["equation_results"].items():
        dist = item["distribution"]
        rows.append(
            {
                "equation": label,
                "description": item["description"],
                "mean": json.dumps(to_jsonable(dist.mean)),
                "covariance_diagonal": json.dumps(to_jsonable(np.diag(dist.covariance))),
                "covariance_eigenvalues": json.dumps(to_jsonable(covariance_eigenvalues(dist.covariance))),
            }
        )
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["equation", "description", "mean", "covariance_diagonal", "covariance_eigenvalues"],
        )
        writer.writeheader()
        writer.writerows(rows)


def build_demo_results(samples: int = 20000, seed: int = 42) -> dict[str, Any]:
    """Build numerical examples for equations (1.20) through (1.25)."""

    rng = np.random.default_rng(seed)

    # Base x distribution used for the unconditioned examples.
    mx = np.array([1.0, -0.5])
    Px = np.array([[2.0, 0.35], [0.35, 1.0]])

    # Independent y distribution used by Eq. (1.20).
    my_ind = np.array([2.0])
    Py_ind = np.array([[0.8]])

    # Linear transformation used by Eq. (1.21): y = A x.
    A_transform = np.array([[1.0, 2.0], [-0.5, 1.0]])

    # Correlated joint normal blocks used by Eq. (1.22).
    my = np.array([0.25])
    Py = np.array([[1.4]])
    Pxy = np.array([[0.55], [-0.30]])
    y_observed = np.array([1.2])

    # Conditional-on-z examples. We freeze z numerically, then treat mx|z and
    # Px|z as already available from a prior estimator step.
    z_value = np.array([3.0])
    mx_given_z = np.array([0.75, -1.25])
    Px_given_z = np.array([[1.25, 0.20], [0.20, 0.70]])
    my_given_z_ind = np.array([-0.40])
    Py_given_z_ind = np.array([[0.50]])
    A_conditional = np.array([[2.0, -1.0]])

    # Correlated conditional joint normal blocks for Eq. (1.25).
    my_given_z = np.array([0.10])
    Py_given_z = np.array([[0.90]])
    Pxy_given_z = np.array([[0.25], [0.15]])
    y_observed_given_z = np.array([-0.60])

    eq_120 = joint_independent_normals(mx, Px, my_ind, Py_ind)
    eq_121 = linear_transform_normal(mx, Px, A_transform)
    eq_122_joint = joint_from_blocks(mx, Px, my, Py, Pxy)
    eq_122 = conditional_joint_normal(mx, Px, my, Py, Pxy, y_observed)

    eq_123 = joint_independent_normals(mx_given_z, Px_given_z, my_given_z_ind, Py_given_z_ind)
    eq_124 = linear_transform_normal(mx_given_z, Px_given_z, A_conditional)
    eq_125_joint = joint_from_blocks(mx_given_z, Px_given_z, my_given_z, Py_given_z, Pxy_given_z)
    eq_125 = conditional_joint_normal(mx_given_z, Px_given_z, my_given_z, Py_given_z, Pxy_given_z, y_observed_given_z)

    # Monte Carlo sanity checks for the first three formulas. These are not the
    # formulas themselves; they simply prove the numbers behave the way expected.
    x_samples = rng.multivariate_normal(mx, Px, size=samples)
    y_ind_samples = rng.multivariate_normal(my_ind, Py_ind, size=samples)
    joint_ind_samples = np.column_stack([x_samples, y_ind_samples])
    transformed_samples = x_samples @ A_transform.T

    joint_corr_samples = rng.multivariate_normal(eq_122_joint.mean, eq_122_joint.covariance, size=samples)
    y_tol = float(np.std(joint_corr_samples[:, -1]) * 0.08)
    near_y = np.abs(joint_corr_samples[:, -1] - y_observed[0]) <= y_tol
    conditional_slice = joint_corr_samples[near_y, : mx.size]

    monte_carlo = {
        "samples_requested": int(samples),
        "seed": int(seed),
        "eq_1_20_joint_independent_sample_stats": sample_stats(joint_ind_samples),
        "eq_1_21_linear_transform_sample_stats": sample_stats(transformed_samples),
        "eq_1_22_conditional_slice_note": (
            "Approximate check only: samples from the joint normal were filtered "
            "to a narrow band around the observed scalar y."
        ),
        "eq_1_22_conditional_slice_tolerance": y_tol,
        "eq_1_22_conditional_slice_count": int(conditional_slice.shape[0]),
        "eq_1_22_conditional_slice_stats": sample_stats(conditional_slice) if conditional_slice.shape[0] > 2 else None,
    }

    return {
        "title": "Rawlings Section 1.4.1 linear systems and normal distributions sandbox",
        "output_directory": "out/normal_distributions",
        "z_value_used_for_conditioned_examples": z_value,
        "equation_results": {
            "1.20": {
                "description": "Joint independent normals: [x; y] has stacked mean and block-diagonal covariance.",
                "inputs": {"mx": mx, "Px": Px, "my": my_ind, "Py": Py_ind},
                "distribution": eq_120,
            },
            "1.21": {
                "description": "Linear transformation of a normal: y = A x has mean A m and covariance A P A.T.",
                "inputs": {"m": mx, "P": Px, "A": A_transform},
                "distribution": eq_121,
            },
            "1.22": {
                "description": "Conditional of a joint normal: p(x | y_observed).",
                "inputs": {"joint": eq_122_joint, "y_observed": y_observed},
                "distribution": eq_122,
            },
            "1.23": {
                "description": "Conditional joint independent normals: p(x,y | z) when p(x | z) is normal and y is independent.",
                "inputs": {"mx_given_z": mx_given_z, "Px_given_z": Px_given_z, "my": my_given_z_ind, "Py": Py_given_z_ind},
                "distribution": eq_123,
            },
            "1.24": {
                "description": "Conditional linear transformation: p(y | z) for y = A x and p(x | z) normal.",
                "inputs": {"m_given_z": mx_given_z, "P_given_z": Px_given_z, "A": A_conditional},
                "distribution": eq_124,
            },
            "1.25": {
                "description": "Conditional of a joint conditional normal: p(x | y_observed, z).",
                "inputs": {"joint_given_z": eq_125_joint, "y_observed_given_z": y_observed_given_z},
                "distribution": eq_125,
            },
        },
        "monte_carlo_sanity_checks": monte_carlo,
    }


def print_compact_summary(results: dict[str, Any]) -> None:
    """Print a readable console summary."""

    print(results["title"])
    print("-" * len(results["title"]))
    for label, item in results["equation_results"].items():
        dist = item["distribution"]
        print(f"Eq. {label}: {item['description']}")
        print(f"  mean = {np.array2string(dist.mean, precision=6, suppress_small=False)}")
        print(f"  covariance =\n{np.array2string(dist.covariance, precision=6, suppress_small=False)}")
        print(f"  eig(covariance) = {np.array2string(covariance_eigenvalues(dist.covariance), precision=6)}")
        print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sandbox for Rawlings Section 1.4.1 normal distribution formulas."
    )
    parser.add_argument(
        "--out",
        default="out/normal_distributions",
        help="Output directory. Default: out/normal_distributions",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=20000,
        help="Monte Carlo samples for sanity checks. Default: 20000",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed. Default: 42")
    parser.add_argument("--pretty", action="store_true", help="Print full JSON after the compact summary")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    results = build_demo_results(samples=args.samples, seed=args.seed)
    results["output_directory"] = str(out_dir)

    json_path = out_dir / "linear_systems_normal_distributions_results.json"
    csv_path = out_dir / "linear_systems_normal_distributions_summary.csv"
    write_json(results, json_path)
    write_summary_csv(results, csv_path)

    print_compact_summary(results)
    print("Files written:")
    print(f"  JSON: {json_path}")
    print(f"  CSV : {csv_path}")

    if args.pretty:
        print("\nFull JSON result:")
        print(json.dumps(to_jsonable(results), indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
