import os, textwrap, numpy as np
from quadraticControl.quadraticTool.apis import RunRequest
from quadraticControl.quadraticTool.app import QuadraticApp

def _write_yaml(path, text):
    with open(path, "w") as f: f.write(text)

def test_ct_siso_ogata(tmp_path):
    yaml = textwrap.dedent("""
    mode: ct-siso-ogata
    a: -1.0
    b: 1.0
    T: 0.1
    N: 5
    x0: 1.0
    S: 1.0
    """).strip()
    infile = tmp_path / "ogata.yaml"
    _write_yaml(infile, yaml)
    outdir = tmp_path / "out"
    req = RunRequest(mode="ct-siso-ogata", infile=str(infile), name="ogata", outdir=str(outdir), plot="none")
    case_dir = QuadraticApp().run(req)
    assert os.path.isdir(case_dir)
    assert os.path.exists(os.path.join(case_dir,"K.csv"))
    assert os.path.exists(os.path.join(case_dir,"x.csv"))
    assert os.path.exists(os.path.join(case_dir,"u.csv"))

def test_ss_lqr_end_to_end(tmp_path):
    yaml = textwrap.dedent("""
    mode: ss-lqr
    G: [[0.9]]
    H: [[0.2]]
    Q: [[1.0]]
    R: [[0.1]]
    """).strip()
    infile = tmp_path / "ss.yaml"
    _write_yaml(infile, yaml)
    outdir = tmp_path / "out"
    req = RunRequest(mode="ss-lqr", infile=str(infile), name="ss", outdir=str(outdir), plot="none")
    case_dir = QuadraticApp().run(req)
    assert os.path.isdir(case_dir)
    assert os.path.exists(os.path.join(case_dir,"P.csv"))
    assert os.path.exists(os.path.join(case_dir,"K.csv"))

def test_servo_lqr_siso(tmp_path):
    # SISO servo with short sim (stabilizable augmented system: make H[1,0] nonzero)
    yaml = textwrap.dedent("""
    mode: servo-lqr
    G: [[0.9, 0.1],
        [0.0, 1.0]]
    H: [[0.1],
        [0.05]]
    C: [[1.0, 0.0]]
    Qx: [[1.0, 0.0],
         [0.0, 0.1]]
    Qi: [[0.5]]
    R: [[0.1]]
    steps: 10
    r: 1.0
    x0: [0.0, 0.0]
    v0: 0.0
    D: 0.0
    """).strip()
    infile = tmp_path / "servo.yaml"
    _write_yaml(infile, yaml)
    outdir = tmp_path / "out"
    req = RunRequest(mode="servo-lqr", infile=str(infile), name="servo", outdir=str(outdir), plot="none")
    case_dir = QuadraticApp().run(req)
    assert os.path.isdir(case_dir)
    for f in ["P.csv","Kx.csv","Ki.csv","K_full.csv","y.csv","u.csv","x1.csv"]:
        assert os.path.exists(os.path.join(case_dir,f))

def test_lyap_analyzer(tmp_path):
    yaml = textwrap.dedent("""
    mode: lyap
    G: [[0.9, 0.0],
        [0.0, 0.8]]
    Q: [[1.0, 0.0],
        [0.0, 1.0]]
    """).strip()
    infile = tmp_path / "lyap.yaml"
    _write_yaml(infile, yaml)
    outdir = tmp_path / "out"
    req = RunRequest(mode="lyap", infile=str(infile), name="lya", outdir=str(outdir), plot="none")
    case_dir = QuadraticApp().run(req)
    assert os.path.isdir(case_dir)
    assert os.path.exists(os.path.join(case_dir,"P.csv"))
    assert os.path.exists(os.path.join(case_dir,"summary.txt"))

def test_unknown_mode_raises(tmp_path):
    yaml = "mode: NOTAMODE\n"
    infile = tmp_path / "bad.yaml"
    _write_yaml(infile, yaml)
    outdir = tmp_path / "out"
    from quadraticControl.quadraticTool.apis import RunRequest
    from quadraticControl.quadraticTool.app import QuadraticApp
    req = RunRequest(mode="notamode", infile=str(infile), name="bad", outdir=str(outdir), plot="none")
    try:
        QuadraticApp().run(req)
        raised = False
    except ValueError:
        raised = True
    assert raised
