# polePlacement/observabilityTool — Observability (Ogata §6)

Object‑oriented refactor of your working `observability.py` into a clean, testable package.

```
polePlacement/observabilityTool/
  app.py
  apis.py
  cli.py            # import shim so `python cli.py` works
  core.py
  design.py
  io.py
  utils.py
  tools/
    class_diagram.py
  tests/
    test_core.py
    test_app.py
  in/
  out/
```

## Usage (from inside the package)
```bash
python cli.py \
  --help
```

### Example 6‑3 (DT, observable)
```bash
python cli.py \
  --A "-1 0; 0 -2" \
  --C "1 5" \
  --discrete \
  --pretty \
  --pbh \
  --save-csv \
  --name ex6_3_case1_obs
```

### Example 6‑4 (DT, unobservable by cancellation)
```bash
python cli.py \
  --A "0 1 0; 0 0 1; -6 -11 -6" \
  --C "4 5 1" \
  --discrete \
  --pretty \
  --pbh \
  --gram \
  --name ex6_4_unobs
```

### CT with Gramian
```bash
python cli.py \
  --A "0 1; -1 0" \
  --C "1 0" \
  --pretty \
  --pbh \
  --gram \
  --name ex6_5_ct
```

### Finite-horizon Gramians
```bash
python cli.py \
  --A "0 1; -1 0" \
  --C "1 0" \
  --finite-ct 5.0 \
  --pretty \
  --name ct_finite
```

### Minimal observable realization
```bash
python cli.py \
  --A "0 1; 0 0" \
  --C "1 0" \
  --minreal \
  --pretty \
  --name mr_demo
```

### Class diagram
```bash
python tools/class_diagram.py \
  --out out
# Produces ./out/observabilityTool_class_diagram.puml
```

### Sphinx

python -m transient_analysis.hurwitzTool.cli sphinx-skel transient_analysis/hurwitzTool/docs
python -m sphinx -b html docs docs/_build/html
open docs/_build/html/index.html
sphinx-autobuild docs docs/_build/html