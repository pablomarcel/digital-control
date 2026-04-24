from __future__ import annotations
import os

__all__ = [
    "ensure_dir",
    "resolve_input_path",
    "resolve_output_path",
    "bin_zero_padded",
    "fmt_code",
]

def ensure_dir(path: str) -> None:
    """
    Ensure the parent directory of `path` exists (safe for file paths).
    If `path` itself is a directory path, it will also be created.
    """
    d = path if os.path.splitext(path)[1] == "" else os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def resolve_input_path(p: str | None, in_dir: str) -> str | None:
    """
    Resolve an input specification:
      - Inline JSON (string starting with '[' or '{') is returned as-is.
      - Absolute paths or existing paths are returned unchanged.
      - Otherwise, we look for the file under `in_dir` and return that if it exists.
      - If it still does not exist, return the original `p` (caller may handle).
    """
    if p is None:
        return None
    s = p.strip()
    if s.startswith('[') or s.startswith('{'):
        return p  # inline JSON stays inline
    if os.path.isabs(p) or os.path.exists(p):
        return p
    cand = os.path.join(in_dir, p)
    return cand if os.path.exists(cand) else p

def resolve_output_path(p: str | None, out_dir: str) -> str | None:
    """
    Resolve an output path according to project policy:
      - Absolute path: keep absolute and ensure parent directory exists.
      - Relative path (even if it contains its own subdirectories like 'foo/bar.txt'):
        place it under `out_dir` and ensure the resulting parent directory exists.
    """
    if p is None:
        return None
    if os.path.isabs(p):
        ensure_dir(p)
        return p
    outp = os.path.join(out_dir, p)
    ensure_dir(outp)
    return outp

def bin_zero_padded(v: int, w: int, group: int | None = None) -> str:
    """
    Return a zero-padded binary string of width `w` for integer `v`.

    By default, no grouping is applied.
    If `group` is a positive integer, insert '_' separators every `group` bits from the MSB side.
    Example:
      bin_zero_padded(0xAB, 8)           -> '10101011'
      bin_zero_padded(0xAB, 8, group=4)  -> '1010_1011'
    """
    s = format(int(v) & ((1 << w) - 1), 'b').zfill(w)
    if not group or group <= 0:
        return s
    parts: list[str] = []
    first = w % group or group
    parts.append(s[:first])
    for i in range(first, w, group):
        parts.append(s[i:i + group])
    return "_".join(parts)

def fmt_code(code: int, nbits: int, radix: str) -> str:
    """
    Format the digital `code` using the given `radix`:
      - 'dec' -> decimal (e.g., '13')
      - 'hex' -> hexadecimal with zero-padding to nbits/4 (e.g., '0x0D')
      - 'bin' -> binary with zero-padding to `nbits` (e.g., '0b00001101')
      - 'all' -> combined 'dec (0b..., 0x...)'

    Grouping underscores are NOT added by default in 'bin'/'all'.
    """
    r = radix.lower()
    if r == 'dec':
        return f"{code}"
    if r == 'hex':
        width_hex = (nbits + 3) // 4
        return f"0x{code:0{width_hex}X}"
    if r == 'bin':
        return f"0b{bin_zero_padded(code, nbits)}"
    if r == 'all':
        width_hex = (nbits + 3) // 4
        return f"{code} (0b{bin_zero_padded(code, nbits)}, 0x{code:0{width_hex}X})"
    return f"{code}"
