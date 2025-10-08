# -*- coding: utf-8 -*-
from __future__ import annotations

import functools
import os
import time
from typing import Callable, Any, Iterable, List
import numpy as np

# ---------- decorators ----------

def log_call(name: str | None = None) -> Callable:
    def deco(fn: Callable) -> Callable:
        label = name or fn.__name__
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            print(f"[{label}] start")
            out = fn(*args, **kwargs)
            print(f"[{label}] done")
            return out
        return wrapper
    return deco

def timer(fn: Callable) -> Callable:
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.time()
        out = fn(*args, **kwargs)
        dt = (time.time() - t0) * 1000.0
        print(f"[{fn.__name__}] {dt:.1f} ms")
        return out
    return wrapper

# ---------- poly helpers ----------

def poly_mul_desc(a: Iterable[float], b: Iterable[float]) -> list[float]:
    """Multiply polynomials given in descending powers."""
    A = list(reversed(list(a)))
    B = list(reversed(list(b)))
    C = np.polynomial.polynomial.polymul(A, B)
    return list(reversed([float(x) for x in C]))

def poly_add_desc(a: Iterable[float], b: Iterable[float]) -> list[float]:
    A = list(reversed(list(a)))
    B = list(reversed(list(b)))
    n = max(len(A), len(B))
    A = [0.0]*(n-len(A)) + A
    B = [0.0]*(n-len(B)) + B
    C = [A[i] + B[i] for i in range(n)]
    return list(reversed([float(x) for x in C]))

def ensure_dir(d: str) -> None:
    os.makedirs(d, exist_ok=True)
