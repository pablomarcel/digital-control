from __future__ import annotations
import os, functools, time
from typing import Callable, Any

def ensure_dir_for(path: str) -> None:
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def is_inline_json(s: str) -> bool:
    if s is None: return False
    t = s.strip()
    return t.startswith('[') or t.startswith('{')

def resolve_input_path(p: str|None, in_dir: str) -> str|None:
    if p is None:
        return None
    if is_inline_json(p):
        return p
    if os.path.isabs(p) or os.path.exists(p):
        return p
    cand = os.path.join(in_dir, p)
    return cand if os.path.exists(cand) else p

def resolve_output_path(p: str|None, out_dir: str) -> str|None:
    if p is None:
        return None
    if os.path.isabs(p) or os.path.dirname(p):
        ensure_dir_for(p)
        return p
    outp = os.path.join(out_dir, p)
    ensure_dir_for(outp)
    return outp

def timecall(fn: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        res = fn(*args, **kwargs)
        dt = (time.perf_counter() - t0) * 1000.0
        try:
            # Attach timing info if the object has .messages list
            if hasattr(res, "messages") and isinstance(res.messages, list):
                res.messages.append(f"{fn.__name__} took {dt:.2f} ms")
        except Exception:
            pass
        return res
    return wrapper

def bin_zero_padded(v: int, w: int, group: int=4) -> str:
    s = format(int(v) & ((1<<w) - 1), 'b').zfill(w)
    if group and group > 0:
        parts, first = [], (w % group or group)
        parts.append(s[:first])
        for i in range(first, w, group):
            parts.append(s[i:i+group])
        return "_".join(parts)
    return s
