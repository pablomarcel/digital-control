#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
io.py — Parsing and I/O helpers for zTransformTool.
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional
import csv
import json
import os

import sympy as sp

from .utils import ensure_out_dir, force_out_path, to_exportable

def parse_subs(kv: Optional[str], sym_tab: Dict[str, sp.Symbol]) -> Dict[sp.Symbol, Any]:
    if not kv:
        return {}
    out = {}
    for pair in kv.replace(';', ',').split(','):
        if not pair.strip():
            continue
        key, val = pair.split('=')
        key = key.strip()
        if key not in sym_tab:
            raise ValueError(f"Unknown symbol in --subs: {key}")
        out[sym_tab[key]] = float(val.strip())
    return out

def parse_coeffs_numeric(s: str) -> List[float]:
    s = s.replace(',', ' ')
    return [float(x) for x in s.split() if x.strip()]

def parse_coeffs_symbolic(s: str, syms: Dict[str, sp.Symbol]) -> List[sp.Expr]:
    s = s.replace(',', ' ')
    return [sp.sympify(tok, locals=syms) for tok in s.split() if tok.strip()]

def export_sequence(rows, values, name: str, export_csv: Optional[str], export_json: Optional[str]) -> None:
    csv_path = force_out_path(export_csv) if export_csv else None
    json_path = force_out_path(export_json) if export_json else None
    if csv_path:
        with open(csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["k", name])
            for kk, yy in zip(rows, values):
                w.writerow([int(kk), to_exportable(yy)])
        print(f"CSV written: {csv_path}")
    if json_path:
        with open(json_path, "w") as f:
            json.dump({"k": list(map(int, rows)), name: [to_exportable(v) for v in values]}, f, indent=2)
        print(f"JSON written: {json_path}")
