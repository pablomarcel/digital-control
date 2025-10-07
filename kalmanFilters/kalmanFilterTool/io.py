from __future__ import annotations
import numpy as np

def parse_matrix(s: str) -> np.ndarray:
    rows = [r.strip() for r in s.strip().split(";") if r.strip()]
    mat = [[complex(x.replace("i","j")) for x in r.replace(",", " ").split()] for r in rows]
    arr = np.array(mat, dtype=complex)
    arr = np.real_if_close(arr, tol=1e8)
    if np.iscomplexobj(arr) and float(np.max(np.abs(arr.imag))) > 1e-12:
        raise ValueError("Matrix has non-negligible imaginary parts.")
    return np.asarray(arr.real, dtype=float)

def parse_vector(s: str) -> np.ndarray:
    arr = np.array([complex(x.replace("i","j")) for x in s.replace(",", " ").split()], dtype=complex)
    arr = np.real_if_close(arr, tol=1e8)
    if np.iscomplexobj(arr) and float(np.max(np.abs(arr.imag))) > 1e-12:
        raise ValueError("Vector has non-negligible imaginary parts.")
    return np.asarray(arr.real, dtype=float).reshape(-1, 1)
