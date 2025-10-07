
from __future__ import annotations
from typing import Optional, Sequence, List
import os, json, csv, numpy as np
from .utils import pkg_in_path, pkg_out_path

def parse_coeffs(s: Optional[str]):
    if s is None: return None
    toks=s.replace(',', ' ').split()
    if not toks: return None
    return np.array([complex(t) for t in toks], complex).real.astype(float)

def parse_complex_list(s: str):
    toks=s.replace(',', ' ').split()
    return [complex(t) for t in toks]

def as_array(x: Optional[Sequence[float]]):
    if x is None: return None
    return np.array(x, float)

def load_json(in_json: Optional[str]) -> dict:
    if not in_json: return {}
    path = pkg_in_path(in_json)
    if not os.path.exists(path): raise FileNotFoundError(f"Input JSON not found: {path}")
    with open(path,'r') as f: return json.load(f)

def save_json_design(path: Optional[str], payload: dict):
    if path is None: return None
    dst = pkg_out_path(path, "rst_design.json")
    with open(dst,'w') as f: json.dump(payload,f,indent=2)
    return dst

def save_csv(path: Optional[str], rows):
    if path is None: return None
    dst = pkg_out_path(path, "rst.csv")
    with open(dst,'w',newline='') as f:
        w=csv.writer(f); w.writerow(["k","r","y","u","v"]); 
        for r in rows: w.writerow(r)
    return dst
