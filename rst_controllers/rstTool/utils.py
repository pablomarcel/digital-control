from __future__ import annotations
import os, functools, time
from typing import Optional, Callable, Any

# Absolute anchors rooted at the rstTool package directory
_PKG_DIR = os.path.abspath(os.path.dirname(__file__))              # .../rst_controllers/rstTool
_IN_DIR  = os.path.join(_PKG_DIR, "in")
_OUT_DIR = os.path.join(_PKG_DIR, "out")

def ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)

def pkg_out_path(name: Optional[str], default_basename: str) -> Optional[str]:
    """
    Always write under rst_controllers/rstTool/out regardless of where the process is launched.
    """
    base = default_basename if not name or not str(name).strip() else os.path.basename(str(name))
    dst = os.path.join(_OUT_DIR, base)
    ensure_dir(dst)
    return dst

def pkg_in_path(name: Optional[str]) -> Optional[str]:
    """
    Resolve input under rst_controllers/rstTool/in, handling a few common spellings:
    - "foo.json"         -> <pkg>/in/foo.json
    - "in/foo.json"      -> <pkg>/in/foo.json
    - "rst_controllers/rstTool/in/foo.json" -> <pkg>/in/foo.json
    Absolute paths are returned untouched.
    """
    if not name:
        return None
    if os.path.isabs(name):
        return name

    clean = name.replace("\\", "/")

    prefix = "rst_controllers/rstTool/in/"
    if clean.startswith(prefix):
        rel = clean[len(prefix):]
        return os.path.join(_IN_DIR, rel)
    if clean.startswith("in/"):
        return os.path.join(_IN_DIR, clean[3:])
    return os.path.join(_IN_DIR, name)

def timeit(label: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def deco(fn):
        @functools.wraps(fn)
        def wrap(*a, **k):
            t0 = time.time()
            r = fn(*a, **k)
            _ = time.time() - t0
            return r
        return wrap
    return deco
