from __future__ import annotations
import os
import re
from typing import List
import sympy as sp

def out_path(default_dir: str, name: str) -> str:
    os.makedirs(default_dir, exist_ok=True)
    return os.path.join(default_dir, name)

def _normalize_i(s: str) -> str:
    return re.sub(r'(?<![A-Za-z0-9_])i(?![A-Za-z0-9_])', 'I', s)

def _strip_outer_brackets(s: str) -> str:
    s = s.strip()
    if s.startswith('[') and s.endswith(']'):
        depth = 0
        ok = True
        for ch in s:
            if ch == '[': depth += 1
            elif ch == ']': depth -= 1
            if depth < 0: ok = False; break
        if ok:
            return s[1:-1].strip()
    return s

def _split_rows(content: str) -> List[str]:
    s = content.strip()
    if '[' in s and ']' in s and ';' not in s:
        rows = []
        i = 0
        while i < len(s):
            if s[i] == '[':
                depth = 1
                j = i + 1
                while j < len(s) and depth > 0:
                    if s[j] == '[': depth += 1
                    elif s[j] == ']': depth -= 1
                    j += 1
                rows.append(s[i+1:j-1].strip())
                i = j
                while i < len(s) and s[i] in ' ,': i += 1
            else:
                i += 1
        if rows: return rows
    rows = []
    depth = 0
    current = []
    for ch in s:
        if ch == '[': depth += 1
        elif ch == ']': depth -= 1
        if ch == ';' and depth == 0:
            rows.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)
    if current: rows.append(''.join(current).strip())
    cleaned = []
    for r in rows:
        r = r.strip()
        if r.startswith('[') and r.endswith(']'):
            r = r[1:-1].strip()
        cleaned.append(r)
    return cleaned

def parse_matrix(s: str) -> sp.Matrix:
    if not isinstance(s, str):
        raise ValueError("Matrix must be provided as a string.")
    raw = _normalize_i(s.replace("\n", " ").strip())
    content = _strip_outer_brackets(raw)
    row_strs = _split_rows(content)
    if not row_strs:
        row_strs = [content]
    data = []
    for r in row_strs:
        toks = [t for t in re.split(r'[,\s]+', r) if t]
        data.append([sp.sympify(t, rational=True) for t in toks])
    if len({len(row) for row in data}) != 1:
        raise ValueError("Matrix rows have inconsistent lengths.")
    return sp.Matrix(data)

def parse_scalar(s: str):
    return sp.sympify(_normalize_i(s), rational=True)

def save_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
