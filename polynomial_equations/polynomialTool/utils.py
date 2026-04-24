from __future__ import annotations
import os
from typing import Optional, Iterable, Tuple, Any

# Package-local roots (used to anchor relative paths like "out/...").
PKG_DIR = os.path.dirname(__file__)
IN_DIR  = os.path.join(PKG_DIR, "in")
OUT_DIR = os.path.join(PKG_DIR, "out")


def ensure_dir_for(path: Optional[str]) -> None:
    """
    Create the parent directory for a file path if needed.
    No-op for None or paths without a directory component.
    """
    if path:
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)


def in_path(*parts: Iterable[str]) -> str:
    """
    Join parts under the package's 'in/' directory.
    Also ensures the parent directory exists.
    """
    p = os.path.join(IN_DIR, *parts)
    ensure_dir_for(p)
    return p


def out_path(*parts: Iterable[str]) -> str:
    """
    Join parts under the package's 'out/' directory.
    Also ensures the parent directory exists.
    """
    p = os.path.join(OUT_DIR, *parts)
    ensure_dir_for(p)
    return p


def _strip_leading_folder(path: str, folder: str) -> str:
    """
    If path starts with 'folder/' or './folder/', strip that prefix and return the remainder.
    Otherwise return path unchanged.
    """
    if path.startswith(folder + os.sep):
        return path[len(folder) + 1 :]
    dotpref = "." + os.sep + folder + os.sep
    if path.startswith(dotpref):
        return path[len(dotpref) :]
    return path


def resolve_in(path: Optional[str]) -> Optional[str]:
    """
    Resolve a user-supplied path intended for inputs.
    - Absolute paths are returned as-is.
    - Paths starting with 'in/' (or './in/') are anchored under the package's IN_DIR.
    - Any other *relative* path is returned unchanged (caller may want CWD).
    """
    if not path:
        return path
    if os.path.isabs(path):
        return path
    # Anchor 'in/...'
    sub = _strip_leading_folder(path, "in")
    if sub != path:
        return in_path(sub)
    return path


def resolve_out(path: Optional[str]) -> Optional[str]:
    """
    Resolve a user-supplied path intended for outputs.
    - Absolute paths are returned as-is.
    - Paths starting with 'out/' (or './out/') are anchored under the package's OUT_DIR.
    - Any other *relative* path is returned unchanged (caller may want CWD),
      but we still ensure its parent dir exists to reduce surprises.
    """
    if not path:
        return path
    if os.path.isabs(path):
        ensure_dir_for(path)
        return path
    # Anchor 'out/...'
    sub = _strip_leading_folder(path, "out")
    if sub != path:
        return out_path(sub)
    # Leave other relative paths alone but make sure parent exists.
    ensure_dir_for(path)
    return path


def log_call(fn):
    """
    Minimal decorator that logs calls. If env POLY_LOG_CALLS=1, include args/kwargs.
    Prints a single line, returns fn(*args, **kwargs).
    """
    from functools import wraps

    @wraps(fn)
    def w(*a: Tuple[Any, ...], **k: Any):
        verbose = os.environ.get("POLY_LOG_CALLS", "0") == "1"
        if verbose:
            print(f"[{fn.__name__}] called with args={a}, kwargs={k}.")
        else:
            print(f"[{fn.__name__}] called.")
        return fn(*a, **k)

    return w
