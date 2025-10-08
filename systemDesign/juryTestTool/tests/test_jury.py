# systemDesign/juryTestTool/tests/test_jury.py
import json
import pathlib
import subprocess
import shlex

PKG_DIR = pathlib.Path(__file__).resolve().parents[1]
CLI = str(PKG_DIR / "cli.py")

def run_cmd(args: str):
    return subprocess.run(
        shlex.split(f"python {CLI} {args}"),
        cwd=str(PKG_DIR),
        capture_output=True,
        text=True
    )

def test_example_44_all():
    r = run_cmd('--coeffs "1, -1.2, 0.07, 0.3, -0.08" --method all --save_json ex44_all.json')
    assert r.returncode == 0, r.stderr
    data = json.loads((PKG_DIR / "out" / "ex44_all.json").read_text())
    assert all(k in data["methods"] for k in ("jury", "schur", "bilinear"))

def test_example_47_range_and_eval():
    in_dir = PKG_DIR / "in"
    in_dir.mkdir(exist_ok=True, parents=True)

    ex47 = {
        "variable": "z",
        "param": "K",
        "coeffs": ["1", "(0.3679*K - 1.3679)", "(0.3679 + 0.2642*K)"]
    }
    (in_dir / "ex47.json").write_text(json.dumps(ex47, indent=2))

    r1 = run_cmd("--json_in ex47.json --method jury --solve_range --save_json ex47_jury.json")
    assert r1.returncode == 0, r1.stderr

    r2 = run_cmd("--json_in ex47.json --method all --eval_K 1.0 --save_json ex47_all_eval.json")
    assert r2.returncode == 0, r2.stderr
