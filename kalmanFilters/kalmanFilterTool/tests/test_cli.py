import os
import sys
import pathlib
import subprocess

def _find_repo_root(start_file: pathlib.Path) -> pathlib.Path:
    """
    Walk up until we find a directory that contains pyproject.toml.
    Fallback: parents[4] (…/digitalControl).
    """
    cur = start_file.resolve().parent
    for _ in range(10):
        if (cur / "pyproject.toml").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return start_file.resolve().parents[4]

_THIS_FILE = pathlib.Path(__file__).resolve()
_REPO_ROOT = _find_repo_root(_THIS_FILE)

def _run_cli(args):
    cmd = [sys.executable, "-m", "kalmanFilters.kalmanFilterTool.cli"] + args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
        env=os.environ.copy(),
    )

def test_cli_help():
    r = _run_cli(["--help"])
    assert r.returncode == 0, r.stderr

def test_cli_smoke_csv(tmp_path):
    out_dir = tmp_path / "out"
    args = [
        "--dt","0.05","--T","1.0","--q","0.25","--r","4.0",
        "--backend","none","--save_csv","kf.csv",
        "--out-dir", str(out_dir)
    ]
    r = _run_cli(args)
    assert r.returncode == 0, r.stderr
    assert (out_dir / "kf.csv").exists()
    assert (out_dir / "kf_meta.json").exists()
