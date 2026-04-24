#!/usr/bin/env python3
from __future__ import annotations
import argparse, os, sys
if __package__ in (None, ""):
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    from introduction.demuxTool.design import render_class_diagram
else:
    from ..design import render_class_diagram

def main():
    ap = argparse.ArgumentParser(description="Render class diagram (DOT/PNG)")
    ap.add_argument("--out", default="out/demuxTool_class_diagram", help="Output path without extension")
    ns = ap.parse_args()
    outp = render_class_diagram(ns.out)
    print(f"Wrote class diagram to {outp}")

if __name__ == "__main__":
    main()
