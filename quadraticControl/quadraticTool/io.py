from __future__ import annotations
import os, csv, yaml
import numpy as np
from typing import Any, Dict, Iterable
from .utils import ensure_dir

def load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r") as f:
        return yaml.safe_load(f)

def save_csv_vector(path: str, vec: Iterable[float]) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        for v in vec:
            vv = float(np.asarray(v).reshape(-1)[0])
            w.writerow([f"{vv:.18e}"])

def save_csv_matrix(path: str, M: np.ndarray) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        for i in range(M.shape[0]):
            row = [f"{float(x):.18e}" for x in np.asarray(M[i,:]).ravel()]
            w.writerow(row)

def write_text(path: str, text: str) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w") as f:
        f.write(text)
