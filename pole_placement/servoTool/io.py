from __future__ import annotations
import csv, json
from typing import Optional, Dict, Any, List
import numpy as np

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

def parse_matrix(s: Optional[str]) -> Optional[np.ndarray]:
    if s is None: return None
    s = s.strip()
    if not s: return None
    rows = []
    for r in s.split(';'):
        r = r.strip()
        if not r: continue
        row = []
        for p in r.replace(',', ' ').split():
            try:
                val = complex(eval(p, {'__builtins__': {}}, {}))
            except Exception:
                val = complex(p)
            row.append(val)
        rows.append(row)
    arr = np.array(rows, dtype=complex)
    if np.all(np.abs(arr.imag) < 1e-12):
        arr = arr.real
    return arr

def force_col(a: Optional[np.ndarray]) -> Optional[np.ndarray]:
    if a is None: return None
    a = np.atleast_2d(a)
    if a.shape[0] < a.shape[1]:
        a = a.T
    return a

def parse_poles(ps: Optional[str]) -> Optional[list[complex]]:
    if ps is None: return None
    s = str(ps).replace(';', ',')
    out: list[complex] = []
    for token in s.split(','):
        token = token.strip()
        if not token: continue
        try:
            out.append(complex(eval(token, {'__builtins__': {}}, {})))
        except Exception:
            out.append(complex(token))
    return out

def load_yaml(path: Optional[str]) -> Dict[str, Any]:
    if not path: return {}
    if yaml is None:
        raise RuntimeError('PyYAML not installed; cannot load --config.')
    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}

def write_json(obj: Dict[str, Any], path: Optional[str]) -> None:
    if not path: return
    def enc(o):
        if isinstance(o, (np.generic,)):
            return o.item()
        try:
            return float(np.real(o))
        except Exception:
            return o
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2, default=enc)

def write_csv_matrix(M: np.ndarray, path: Optional[str]) -> None:
    if not path: return
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        for r in np.atleast_2d(M):
            writer.writerow([np.real_if_close(v).item() for v in r])

def write_csv_series(y: List[float], path: Optional[str]) -> None:
    if not path: return
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['k', 'y'])
        for k, v in enumerate(y):
            writer.writerow([k, float(v)])
