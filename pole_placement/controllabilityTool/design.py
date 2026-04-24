from __future__ import annotations
import os, json
from typing import Any, Dict, List, Optional
import numpy as np

def fmt_matrix(M: np.ndarray, width: int = 10, prec: int = 6) -> str:
    fmt = f"{{:>{width}.{prec}g}}"
    rows = []
    for r in M:
        rows.append(" ".join(fmt.format(complex(v)) for v in r))
    return "\n".join(rows)

def write_csv(path: str, M: np.ndarray) -> None:
    np.savetxt(path, np.real_if_close(M), delimiter=",")

def write_json(path: str, obj: Dict[str, Any]) -> None:
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)

def write_text(path: str, text: str) -> None:
    with open(path, "w") as f:
        f.write(text)
