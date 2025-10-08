# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import sys
import json
import platform
import pathlib
import subprocess

def _dump_block(title: str, payload) -> str:
    try:
        body = json.dumps(payload, indent=2, sort_keys=True, default=str)
    except Exception:
        body = str(payload)
    return f"\n==== {title} ====\n{body}\n"

def _list_dir(p: pathlib.Path, depth: int = 2):
    lines = []
    base = p
    try:
        for root, dirs, files in os.walk(base):
            r = pathlib.Path(root)
            rel = r.relative_to(base)
            if len(rel.parts) > depth:
                continue
            lines.append(str(r))
            for f in files:
                if f in {"cli.py", "RUNS.md"} or "zGridTool" in str(r):
                    lines.append(str(r / f))
    except Exception as e:
        lines.append(f"(error listing {p}: {e})")
    return lines

def test_cli_help_runs():
    here = pathlib.Path(__file__).resolve()

    # Primary candidate: tests/.. = zGridTool/, so cli.py is sibling of tests/
    candidates = [
        here.parents[1] / "cli.py",                             # .../zGridTool/cli.py
        here.parents[2] / "zGridTool" / "cli.py",               # .../systemDesign/zGridTool/cli.py
        here.parents[2] / "systemDesign" / "zGridTool" / "cli.py",
        here.parents[3] / "systemDesign" / "zGridTool" / "cli.py",
    ]

    cli = None
    tried = []
    for c in candidates:
        tried.append(str(c))
        if c.exists():
            cli = c
            break

    env_info = {
        "python": sys.executable,
        "python_version": sys.version,
        "platform": platform.platform(),
        "cwd": os.getcwd(),
        "this_test": str(here),
        "searched_cli_paths": tried,
    }

    if cli is None:
        # Tree snapshots to help diagnose path issues
        snapshots = {
            "tree_tests_parent": _list_dir(here.parents[1]),
            "tree_systemDesign": _list_dir(here.parents[2]),
            "tree_project_root_guess": _list_dir(here.parents[3]) if len(here.parents) >= 4 else []
        }
        raise AssertionError(
            _dump_block("ENV", env_info) +
            _dump_block("SNAPSHOTS", snapshots) +
            "\nFATAL: Could not locate systemDesign/zGridTool/cli.py\n"
        )

    # Run from inside the package dir so the import shim in cli.py works
    pkg_dir = cli.parent

    # Build PYTHONPATH to include the project root (…/systemDesign/..)
    project_root = pkg_dir.parent.parent
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(project_root), env.get("PYTHONPATH","")])

    # Pre-run directory listings for context
    ls_pkg = sorted(os.listdir(pkg_dir))
    ls_parent = sorted(os.listdir(pkg_dir.parent))

    # Execute --help
    cmd = [sys.executable, str(cli), "--help"]
    res = subprocess.run(cmd, cwd=str(pkg_dir), env=env, capture_output=True, text=True)

    debug = (
        _dump_block("ENV", env_info) +
        _dump_block("PKG_DIR", str(pkg_dir)) +
        _dump_block("PROJECT_ROOT", str(project_root)) +
        _dump_block("LS_PKG_DIR", ls_pkg) +
        _dump_block("LS_PKG_PARENT", ls_parent) +
        _dump_block("COMMAND", cmd) +
        _dump_block("RETURNCODE", res.returncode) +
        _dump_block("STDOUT", res.stdout) +
        _dump_block("STDERR", res.stderr)
    )

    assert res.returncode == 0, "CLI --help failed.\n" + debug
    # Basic sanity check
    assert ("z-grid tool" in res.stdout.lower()) or ("usage:" in res.stdout.lower()), debug
