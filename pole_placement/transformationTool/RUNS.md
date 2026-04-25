
# polePlacement.transformationTool — Canonical-form Transforms (Ogata §6‑4)

Run **from inside** `digitalControl/polePlacement/transformationTool`:

```bash
python cli.py --help
```

Inputs: `./in/` (optional convention)  
Outputs: `./out/`

## Examples

### 1) CCF (SISO)
```bash
python cli.py \
  --A "0 1; -2 -3" \
  --B "0; 1" \
  --C "1 0" \
  --to-ccf \
  --pretty \
  --check-invariance \
  --show-tf \
  --save-json \
  --save-csv \
  --name ccf_demo
```

### 2) OCF (SISO, via duality)
```bash
python cli.py \
  --A "0 1; -2 -3" \
  --B "0; 1" \
  --C "1 5" \
  --to-ocf \
  --pretty \
  --check-invariance \
  --save-json \
  --save-csv \
  --name ocf_demo
```

### 3) Diagonal (distinct eigenvalues)
```bash
python cli.py \
  --A "-1 0; 0 -2" \
  --B "0;1" \
  --C "1 0" \
  --to-diag \
  --pretty \
  --save-json \
  --save-csv \
  --name diag_demo
```

### 4) Jordan (symbolic via SymPy)
```bash
python cli.py \
  --A "0 1 0; 0 0 1; 0 0 0" \
  --B "0; 0; 1" \
  --C "1 0 0" \
  --to-jordan \
  --pretty \
  --save-json \
  --save-csv \
  --name jordan_demo
```

### 5) JSON in/out
```
in/sys_tf.json
{
  "A": [[0,1],[-2,-3]],
  "B": [[0],[1]],
  "C": [[1,5]],
  "D": [[0]]
}
```

Run:
```bash
python cli.py \
  --json in/sys_tf.json \
  --to-ccf \
  --to-ocf \
  --pretty \
  --name both_from_json \
  --save-json
```

### Sphinx

python -m pole_placement.transformationTool.cli sphinx-skel pole_placement/transformationTool/docs
python -m sphinx -b html docs docs/_build/html
open docs/_build/html/index.html
sphinx-autobuild docs docs/_build/html