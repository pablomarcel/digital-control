#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
utils.py — Shared utilities for zTransformTool.
"""
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple, Iterable

import sympy as sp

DEFAULT_OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
DEFAULT_IN_DIR  = os.path.join(os.path.dirname(__file__), "in")

def ensure_out_dir(path: Optional[str] = None) -> str:
    """
    Ensure the out directory exists. If path is provided and is absolute, ensure its parent exists and return path.
    If path is a relative filename, rewrite to our package out/ directory.
    """
    # Absolute path: respect as-is, ensure parent exists
    if path and os.path.isabs(path):
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        return path
    # else: ensure package out/
    os.makedirs(DEFAULT_OUT_DIR, exist_ok=True)
    return DEFAULT_OUT_DIR

def force_out_path(path: Optional[str]) -> Optional[str]:
    """
    Map a possibly-relative path to the package out/ folder; absolute paths are respected.
    """
    if not path:
        return None
    if os.path.isabs(path):
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        return path
    out_dir = ensure_out_dir()
    return os.path.join(out_dir, os.path.basename(path))

def pbox(title: str, obj, latex: bool = False) -> str:
    """
    Format a pretty box string (returned). The App decides whether to print it.
    """
    if latex:
        body = sp.latex(obj)
    else:
        body = sp.pretty(obj, use_unicode=True)
    line = "=" * len(title)
    return f"\n{line}\n{title}\n{line}\n{body}\n"

def to_exportable(x):
    """
    Convert a SymPy expression to a JSON/CSV friendly representation.
    """
    try:
        xn = sp.N(x)
        if getattr(xn, "is_real", False):
            return float(xn)
        return str(x)
    except Exception:
        return str(x)

def symbol_table() -> Dict[str, sp.Symbol]:
    """
    Canonical symbol table used across the tool.
    """
    k = sp.symbols('k', integer=True, nonnegative=True)
    z, T, w, a, b, t = sp.symbols('z T w a b t', real=True)
    return {'k': k, 'z': z, 'T': T, 'w': w, 'a': a, 'b': b, 't': t, 'I': sp.I}
