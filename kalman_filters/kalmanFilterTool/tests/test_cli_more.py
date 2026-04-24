
import sys, subprocess, pathlib, os

def _repo_root(start: pathlib.Path) -> pathlib.Path:
    cur = start.resolve().parent
    for _ in range(10):
        if (cur / "pyproject.toml").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return start.resolve().parents[4]

def test_cli_custom_model(tmp_path):
    repo_root = _repo_root(pathlib.Path(__file__))
    out_dir = tmp_path / "out"
    cmd = [
        sys.executable, "-m", "kalman_filters.kalmanFilterTool.cli",
        "--A","1 0.05; 0 1",
        "--B","0.00125; 0.05",
        "--C","1 0",
        "--G","0 1",            # row that should auto-transpose
        "--Q","0.01",           # scalar + G => input-form
        "--R","4",              # scalar; p=1 so stays 1x1
        "--backend","none",
        "--save_csv","kf_custom.csv",
        "--out-dir", str(out_dir),
        "--T","0.5",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(repo_root))
    assert r.returncode == 0, r.stderr
    assert (out_dir / "kf_custom.csv").exists()
    assert (out_dir / "kf_meta.json").exists()
