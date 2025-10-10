
import sys, subprocess, json, pathlib, os

def run_cli(args, cwd):
    return subprocess.run([sys.executable, "cli.py"] + args, cwd=cwd, text=True, capture_output=True, check=True)

def test_cli_help(capsys):
    # Run as a subprocess to match real usage, from package dir
    pkg_dir = pathlib.Path(__file__).resolve().parents[1]
    res = subprocess.run([sys.executable, "cli.py", "--help"], cwd=str(pkg_dir), text=True, capture_output=True)
    assert res.returncode == 0
    assert "intro.muxTool" in res.stdout

def test_cli_with_csv_and_outdir(tmp_path):
    pkg_dir = pathlib.Path(__file__).resolve().parents[1]
    # Write a temp csv in package in/ and call with relative name and custom outdir (absolute)
    csvp = pkg_dir / "in" / "test_vectors.csv"
    csvp.write_text("sel,d0,d1,d2,d3\n0,1,2,3,4\n1,5,6,7,8\n")
    out_csv = "r_cli.csv"
    out_vcd = "r_cli.vcd"
    res = run_cli(["--csv", "test_vectors.csv", "--out", out_csv, "--trace", out_vcd, "--outdir", str(tmp_path)], cwd=str(pkg_dir))
    assert (tmp_path / out_csv).exists()
    assert (tmp_path / out_vcd).exists()

def test_cli_with_inline_json(tmp_path):
    pkg_dir = pathlib.Path(__file__).resolve().parents[1]
    vectors = json.dumps([{"sel":0,"d0":1,"d1":2,"d2":3,"d3":4}])
    res = run_cli(["--json", vectors, "--outdir", str(tmp_path), "--out", "x.csv"], cwd=str(pkg_dir))
    assert (tmp_path / "x.csv").exists()
