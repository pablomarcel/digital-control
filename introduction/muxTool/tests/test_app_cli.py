
import json, os, tempfile, subprocess, sys, pathlib

def run_cli(args, cwd):
    cmd = [sys.executable, "cli.py"] + args
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)

def test_cli_runs_with_inline_json_and_writes(tmp_path):
    # Build inline vectors
    vectors = [
        {"sel": 0, "d0": 1, "d1": 2, "d2": 3, "d3": 4},
        {"sel": 1, "d0": 5, "d1": 6, "d2": 7, "d3": 8},
    ]
    json_inline = json.dumps(vectors)

    # Prepare out paths (relative -> out/)
    pkg_dir = pathlib.Path(__file__).resolve().parents[1]
    out_csv = "results.csv"
    out_vcd = "mux.vcd"

    # Run CLI from inside the package
    res = run_cli(["--json", json_inline, "--out", out_csv, "--trace", out_vcd], cwd=str(pkg_dir))

    # Check outputs landed under out/
    out_dir = pkg_dir / "out"
    assert (out_dir / out_csv).exists()
    assert (out_dir / out_vcd).exists()

    # Quick sanity check on CSV contents
    data = (out_dir / out_csv).read_text().strip().splitlines()
    assert data[0].split(",")[:2] == ["cycle","sel"]
