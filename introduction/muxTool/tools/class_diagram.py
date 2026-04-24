#!/usr/bin/env python3
from __future__ import annotations

import os, sys, inspect, argparse, textwrap

# Import shim for running from inside the package
if __package__ in (None, ""):
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    from introduction.muxTool.core import MuxCore
    from introduction.muxTool.app import MuxApp
    from introduction.muxTool.apis import RunRequest, RunResult
else:
    from ..core import MuxCore
    from ..app import MuxApp
    from ..apis import RunRequest, RunResult

def mermaid_class_block() -> str:
    classes = [MuxCore, MuxApp, RunRequest, RunResult]
    lines = ["classDiagram"]
    for cls in classes:
        name = cls.__name__
        lines.append(f"class {name}")
        # show attributes for dataclasses
        if hasattr(cls, "__dataclass_fields__"):
            for field, fobj in cls.__dataclass_fields__.items():  # type: ignore[attr-defined]
                lines.append(f"  {name} : {field}")
    # relationships (manual for clarity)
    lines.append("MuxApp --> MuxCore : uses")
    lines.append("MuxApp --> RunRequest : consumes")
    lines.append("MuxApp --> RunResult : returns")
    return "\n".join(lines)

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Generate Mermaid class diagram for muxTool")
    ap.add_argument("--out", required=True, help="output path without extension; writes .mmd")
    ns = ap.parse_args(argv)
    out_path = ns.out if ns.out.endswith(".mmd") else ns.out + ".mmd"
    content = mermaid_class_block()
    os.makedirs(os.path.dirname(out_path), exist_ok=True) if os.path.dirname(out_path) else None
    with open(out_path, "w") as f:
        f.write(content + "\n")
    print(f"Wrote Mermaid diagram to {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
