# polePlacement.controllabilityTool — RUNS

Run from inside the package:

```bash
cd digitalControl/pole_placement/controllabilityTool
python cli.py \
  --help
```

## A) Continuous‑time (PBH + ∞‑Gramian + CSV/JSON)
```bash
python cli.py \
  --A "0 1; -2 -3" \
  --B "0; 1" \
  --name ct_ex \
  --pbh \
  --gram \
  --pretty \
  --save-csv \
  --save-json \
  --save-gram
```

## B) Finite‑horizon CT 5 s
```bash
python cli.py \
  --A "0 1; -2 -3" \
  --B "0; 1" \
  --finite-ct 5.0 \
  --name ct_finite5 \
  --pretty \
  --save-gram
```

## C) Discrete‑time marginal (finite N=50)
```bash
python cli.py \
  --A "1 0.05; 0 1" \
  --B "0.00125; 0.05" \
  --discrete \
  --finite-dt 50 \
  --name dt_finite50 \
  --pbh \
  --pretty \
  --save-gram \
  --save-json
```

## D) Output controllability (no D)
```bash
python cli.py \
  --A "0 1; -2 -3" \
  --B "0; 1" \
  --C "1 0" \
  --output-ctrb \
  --pretty \
  --save-output-csv \
  --name ex_out_ct
```

## E) Minimal realization demo
```bash
python cli.py \
  --A "0 1 0; 0 0 0; 0 0 -1" \
  --B "0; 0; 1" \
  --name minr_demo \
  --minreal \
  --pretty \
  --save-json
```

## F) JSON‑driven
Create `in/sys.json`:
```json
{
  "A": [[1.0, 0.05], [0.0, 1.0]],
  "B": [[0.00125], [0.05]],
  "discrete": true
}
```

Run:
```bash
python cli.py \
  --json in/sys.json \
  --name sys \
  --pbh \
  --pretty \
  --finite-dt 100 \
  --save-gram \
  --save-json
```

### Sphinx

python -m pole_placement.controllabilityTool.cli sphinx-skel pole_placement/controllabilityTool/docs
python -m sphinx -b html docs docs/_build/html
open docs/_build/html/index.html
sphinx-autobuild docs docs/_build/html