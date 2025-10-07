from __future__ import annotations
import csv, glob, json, os
from typing import Dict, List, Optional, Sequence
import numpy as np

def expand_files(patterns: Sequence[str]) -> List[str]:
    out: List[str] = []
    for p in patterns:
        matched = glob.glob(p)
        if matched:
            out.extend(sorted(matched))
        else:
            out.append(p)  # trust as literal
    return out

def load_csv(path: str) -> Dict[str, np.ndarray]:
    # Load CSV with header k,r,y,u,v; return dict with e=r-y.
    with open(path, "r", newline="") as f:
        rd = csv.reader(f)
        header = next(rd)
        header = [h.strip() for h in header]
        needed = ["k", "r", "y", "u", "v"]
        if header[:5] != needed:
            data = np.genfromtxt(path, delimiter=",", names=True)
            k = np.array(data["k"], dtype=float)
            r = np.array(data["r"], dtype=float)
            y = np.array(data["y"], dtype=float)
            u = np.array(data["u"], dtype=float)
            v = np.array(data["v"], dtype=float)
        else:
            rows = [[float(x) for x in row[:5]] for row in rd]
            arr = np.array(rows, dtype=float)
            if arr.ndim == 1:
                arr = arr[None, :]
            k, r, y, u, v = [arr[:, i] for i in range(5)]
    e = r - y
    return dict(k=k, r=r, y=y, u=u, v=v, e=e)

def load_design_json(path: Optional[str]) -> Optional[dict]:
    if not path:
        return None
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)
