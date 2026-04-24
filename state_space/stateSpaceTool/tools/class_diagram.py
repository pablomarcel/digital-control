from __future__ import annotations
import os, sys, logging, pprint
from textwrap import dedent
import argparse
from typing import List, Optional

LOG = logging.getLogger("state_space.stateSpaceTool.tools.class_diagram")
if not LOG.handlers:
    # Do not override global config, just ensure at least one handler for direct runs.
    h = logging.StreamHandler(sys.stderr)
    fmt = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    h.setFormatter(fmt)
    LOG.addHandler(h)
LOG.setLevel(logging.DEBUG)

PUML = dedent(r"""
@startuml stateSpaceTool_class_diagram
skinparam classAttributeIconSize 0
title state_space.stateSpaceTool - Class Diagram

package state_space.stateSpaceTool {
  class StateSpaceApp {
    + run(req: RunRequest) : RunResult
    - _J(M)
  }

  class RunRequest {
    + form: str
    + num: str
    + den: str
    + zeros: str
    + poles: str
    + gain: float
    + forms: str
    + realblocks: bool
    + dt: float
    + latex: bool
    + latex_out: str
    + json_out: str
    + check: str
    + quiet: bool
  }

  class RunResult {
    + realizations: dict
    + latex: str
    + check_log: str
  }
}

StateSpaceApp --> RunRequest
StateSpaceApp --> RunResult
@enduml
""")

def _env_snapshot():
    keys = ["PYTEST_CURRENT_TEST", "PWD", "CI", "GITHUB_ACTIONS"]
    return {k: os.environ.get(k) for k in keys}

def main(argv: Optional[List[str]] = None):
    LOG.debug("=== class_diagram.main() invoked ===")
    LOG.debug("cwd: %s", os.getcwd())
    LOG.debug("sys.argv: %s", pprint.pformat(sys.argv))
    LOG.debug("incoming argv param: %s", pprint.pformat(argv))
    LOG.debug("env snapshot: %s", _env_snapshot())

    # If called under pytest without explicit argv, avoid pytest arg bleed.
    if argv is None and os.environ.get("PYTEST_CURRENT_TEST"):
        LOG.debug("Detected pytest and argv is None; overriding argv=[] to avoid pytest args bleed")
        argv = []

    parser = argparse.ArgumentParser(prog="stateSpaceTool.class_diagram")
    parser.add_argument("--out", type=str, default="out", help="Output directory for PUML file")
    args = parser.parse_args(argv)

    LOG.debug("Parsed args: %s", args)
    os.makedirs(args.out, exist_ok=True)
    fname = os.path.join(args.out, "stateSpaceTool_class_diagram.puml")
    LOG.debug("About to write PUML to: %s", fname)

    with open(fname, "w", encoding="utf-8") as f:
        f.write(PUML)

    LOG.info("Wrote %s", fname)
    print(f"Wrote {fname}")

if __name__ == "__main__":
    main()
