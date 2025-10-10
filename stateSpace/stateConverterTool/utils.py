from __future__ import annotations
import functools
from typing import Callable
import time

def step(label: str) -> Callable:
    """
    Decorator to mark a pipeline step (for future progress hooks/logging).
    Currently a no-op that records elapsed time as an attribute.
    """
    def deco(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            t0 = time.time()
            out = fn(*args, **kwargs)
            setattr(wrapper, "_last_elapsed", time.time() - t0)
            return out
        wrapper._step_label = label
        return wrapper
    return deco
