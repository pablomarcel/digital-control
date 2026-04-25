# RST Tool — Exhaustive Run Commands (from inside the package)

These examples assume your shell **cwd is the package folder**:
```
cd rstControllers/rstTool
```

All outputs are **forced** into `rstControllers/rstTool/out/`. Inputs are looked up under `rstControllers/rstTool/in/` unless you pass an absolute path.

---

## 0) Help & sanity

Show CLI help (import-shim works when run in-place):
```bash
python cli.py --help
```

Run via the module path (works from anywhere; shown here for completeness):
```bash
python -m rst_controllers.rstTool.cli --help
```

---

## 1) Minimal unity step-tracking (two poles at 0.6)

```bash
python cli.py --A "1 -0.8" --B "0.5" --d 1   --poles "0.6 0.6"   --Tmode unity_dc --pretty   --step 120 --save_csv --export_json
```
- Writes `out/rst.csv` and `out/rst_design.json`.

Custom output names:
```bash
python cli.py --A "1 -0.8" --B "0.5" --d 1   --poles "0.6 0.6" --Tmode unity_dc   --save_csv my_unity.csv --export_json my_unity.json
```

---

## 2) Prefilter T = K·Ac (Ac·Ao = Acl)

```bash
python cli.py --A "1 -0.8" --B "0.5" --d 1   --Ac "1 -1.2 0.36" --Ao "1"   --Tmode ac --pretty --export_json ac_design.json
```

Use only `Ao` and derive `Ac = Acl/Ao` from poles:
```bash
python cli.py --A "1 -0.8" --B "0.5" --d 1   --poles "0.6 0.6" --Ao "1"   --Tmode ac --pretty
```

---

## 3) Integrator + extra pole (unity tracking via T(1)=R(1))

```bash
python cli.py --A "1 -0.8" --B "0.5" --d 1   --poles "0.6 0.6 0.3" --integrator   --Tmode unity_dc --pretty   --step 200 --save_csv rst_int.csv
```

---

## 4) s-plane poles (map with z = exp(s·Ts))

```bash
python cli.py --A "1 -0.8" --B "0.5" --d 1 --Ts 0.1   --spoles "-3+4j -3-4j" --Ao "1 -0.4"   --Tmode ac --pretty --export_json s_map.json
```

---

## 5) Direct closed-loop polynomial Acl

```bash
python cli.py --A "1 -0.8" --B "0.5" --d 1   --Acl "1 -1.2 0.36"   --pretty --export_json acl_direct.json
```

---

## 6) Degree overrides and allocation

Request specific degrees; solver keeps your targets by padding extras with zeros if needed:
```bash
python cli.py --A "1 -0.8" --B "0.5" --d 1   --poles "0.6 0.6"   --degS 1 --degR 0 --pretty       # valid square combo example
```

Allocate extra order into **R** instead of **S**:
```bash
python cli.py --A "1 -0.8" --B "0.5" --d 1   --poles "0.6 0.6" --alloc R --pretty
```

Aggressive override with integrator (exercise safe padding):
```bash
python cli.py --A "1 -0.8" --B "0.5" --d 1   --poles "0.6 0.6 0.3" --integrator   --degS 4 --degR 3 --pretty
```

---

## 7) Manual prefilter T(q)

```bash
python cli.py --A "1 -0.8" --B "0.5" --d 1 --poles "0.6 0.6"   --Tmode manual --T "0.9 0.1" --pretty
```

---

## 8) JSON-driven run (load spec from `in/`)

1) Create `in/my_spec.json` (example minimal):
```json
{
  "plant": {"A": [1.0, -0.8], "B": [0.5], "d": 1},
  "target": {"Acl": [1.0, -1.2, 0.36]},
  "controller": {"Tmode": "unity_dc", "integrator": false},
  "simulation": {"N": 100, "r_step": 1.0},
  "notes": {"Ts": 1.0}
}
```

2) Run with `--in_json` (relative path resolves to `rstControllers/rstTool/in/`):
```bash
python cli.py --in_json my_spec.json --pretty --export_json json_out.json --save_csv json_out.csv
```

You can still **override** fields via CLI; CLI values win over JSON.

---

## 9) Disturbance, noise, and length variants

Disturbance step at k0 with measurement noise:
```bash
python cli.py --A "1 -0.8" --B "0.5" --d 1 --poles "0.6 0.6"   --v_step 0.2 --v_k0 80 --noise 0.01 --step 200 --pretty
```

Short simulations for quick checks:
```bash
python cli.py --A "1 -0.8" --B "0.5" --d 1 --poles "0.8 0.8"   --step 40 --pretty
```

---

## 10) Run tests (from repo root or from here)

From repo root (uses repo’s `pytest.ini`):
```bash
pytest rst_controllers/rstTool/tests
```

Ad-hoc coverage focused on rstTool only (ignores repo addopts):
```bash
pytest rst_controllers/rstTool/tests   --override-ini addopts=   --cov=rst_controllers.rstTool   --cov-report=term-missing
```

---

## 11) Class diagram (PlantUML)

```bash
python tools/class_diagram.py
# -> out/rstTool_class_diagram.puml
```

---

## 12) Equivalent commands when NOT in this folder

From the **repo root**, prefix with the module path:
```bash
python -m rst_controllers.rstTool.cli --A "1 -0.8" --B "0.5" --d 1 --poles "0.6 0.6" --Tmode unity_dc --pretty
```

Both forms are supported by the import shim in `cli.py`.

### Sphinx

python -m rst_controllers.rstTool.cli sphinx-skel rst_controllers/rstTool/docs
python -m sphinx -b html docs docs/_build/html
open docs/_build/html/index.html
sphinx-autobuild docs docs/_build/html