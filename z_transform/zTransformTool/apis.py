#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
apis.py — Public API dataclasses for zTransformTool.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class RunRequest:
    mode: str  # 'forward'|'forward_xt'|'inverse'|'series'|'residuez'|'tf'|'diff'
    expr: Optional[str] = None
    xt: Optional[str] = None
    X: Optional[str] = None
    subs: Optional[str] = None
    N: Optional[int] = None
    latex: bool = False
    export_csv: Optional[str] = None
    export_json: Optional[str] = None
    # residuez / tf
    num: Optional[str] = None
    den: Optional[str] = None
    dt: float = 1.0
    impulse: bool = False
    step: bool = False
    u: Optional[str] = None
    # diff
    rec: Optional[str] = None
    a: Optional[str] = None
    rhs: Optional[str] = None
    ics: Optional[str] = None
