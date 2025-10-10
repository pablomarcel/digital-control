from __future__ import annotations
import os, json

def ensure_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def looks_inline_json(s: str) -> bool:
    t = s.strip()
    return t.startswith('[') or t.startswith('{')

def resolve_input_path(p: str | None, in_dir: str) -> str | None:
    if p is None:
        return None
    if looks_inline_json(p):
        return p
    if os.path.isabs(p) or os.path.exists(p):
        return p
    cand = os.path.join(in_dir, p)
    return cand if os.path.exists(cand) else p

def resolve_output_path(p: str | None, out_dir: str) -> str | None:
    if p is None:
        return None
    if os.path.isabs(p) or os.path.dirname(p):
        ensure_dir(p)
        return p
    outp = os.path.join(out_dir, p)
    ensure_dir(outp)
    return outp

def mask(v: int, bits: int) -> int:
    return int(v) & ((1 << bits) - 1)
