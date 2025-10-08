#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
design.py — Presentation helpers for zTransformTool (formatting, strings).
"""
from __future__ import annotations
import sympy as sp
from typing import Any

from .utils import pbox

def box(title: str, obj: Any, latex: bool = False) -> str:
    return pbox(title, obj, latex)

def as_text(obj: Any, latex: bool = False) -> str:
    return sp.latex(obj) if latex else sp.pretty(obj, use_unicode=True)
