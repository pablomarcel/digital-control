from __future__ import annotations
import os, csv, math
from typing import Dict, List

_TS_MULT = {'s':1.0,'ms':1e-3,'us':1e-6,'ns':1e-9,'ps':1e-12,'fs':1e-15}
_UNIT_SCALE = {'s':1.0,'ms':1e3,'us':1e6,'ns':1e9}

def resolve_input_path(p: str, in_dir: str) -> str:
    if os.path.isabs(p) or os.path.exists(p):
        return p
    cand = os.path.join(in_dir, p)
    return cand if os.path.exists(cand) else p

def resolve_output_path(p: str | None, out_dir: str) -> str | None:
    """
    Policy:
    - Absolute paths: return as-is (ensure parent dir exists).
    - Relative paths (even with a subdirectory like 'sub/out.csv'): join with out_dir.
    """
    if not p:
        return None
    if os.path.isabs(p):
        d = os.path.dirname(p)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
        return p
    # always place relative outputs under out_dir
    outp = os.path.join(out_dir, p)
    d = os.path.dirname(outp)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    return outp

def export_csv(csv_path: str, times_sec: List[float], series: Dict[str, List[float]], csv_units: str) -> None:
    scale = _UNIT_SCALE[csv_units]
    cols = list(series.keys())
    with open(csv_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow([f"time_{csv_units}"] + cols)
        for i in range(len(times_sec)):
            row = [f"{times_sec[i]*scale:.12g}"]
            for c in cols:
                v = series[c][i]
                if isinstance(v, float) and math.isnan(v):
                    row.append("NaN")
                else:
                    row.append(v)
            w.writerow(row)
    print(f"Wrote CSV to {csv_path}")

def unit_scale_map() -> Dict[str, float]:
    return dict(_UNIT_SCALE)

def timescale_map() -> Dict[str, float]:
    return dict(_TS_MULT)
