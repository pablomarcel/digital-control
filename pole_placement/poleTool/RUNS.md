# RUNS — `polePlacement/poleTool` (Discrete-Time Pole Placement, Ogata §6‑5)

**Run all commands from *inside* this package directory:**
```bash
cd digitalControl/pole_placement/poleTool
```

Outputs default to `./out/` unless you pass `--outdir`.

## Quick help
```bash
python cli.py \
  --help
```

## A) SISO — Ackermann (Ogata Ex. 6‑6) — MPL dots
```bash
python cli.py \
  --A "0 1; -0.16 -1" \
  --B "0; 1" \
  --C "1 0" \
  --poles "0.5+0.5j,0.5-0.5j" \
  --plot mpl \
  --style dots \
  --pretty \
  --save_json \
  --save_csv \
  --name ex6_6_ack_mpl
```

## B) SISO — Ackermann — MPL stairs
```bash
python cli.py \
  --A "0 1; -0.16 -1" \
  --B "0; 1" \
  --C "1 0" \
  --poles "0.5+0.5j,0.5-0.5j" \
  --plot mpl \
  --style stairs \
  --save_json \
  --save_csv \
  --name ex6_6_ack_mpl_stairs
```

## C) SISO — Ackermann — Plotly (connected)
```bash
python cli.py \
  --A "0 1; -0.16 -1" \
  --B "0; 1" \
  --C "1 0" \
  --poles "0.5+0.5j,0.5-0.5j" \
  --plot plotly \
  --style connected \
  --save_json \
  --save_csv \
  --name ex6_6_ack_plotly
```

## D) SISO — Ogata eigenvector method (same poles as Ex. 6‑6)
```bash
python cli.py \
  --A "0 1; -0.16 -1" \
  --B "0; 1" \
  --C "1 0" \
  --poles "0.5+0.5j,0.5-0.5j" \
  --method ogata \
  --plot none \
  --pretty \
  --name ex6_6_ogata
```

## E) SISO — Explicit eigenvector method (`--method eigs`)
```bash
python cli.py \
  --A "0 1; -0.16 -1" \
  --B "0; 1" \
  --C "1 0" \
  --poles "0.4+0.3j,0.4-0.3j" \
  --method eigs \
  --plot none \
  --pretty \
  --name eigs_siso
```

## F) MIMO — SciPy / python‑control `place` (falls back to SISO eigs if needed)
```bash
python cli.py \
  --A "0 1 0; 0 0 1; -1.2 -1.3 -0.4" \
  --B "1 0; 0 1; 1 1" \
  --C "1 0 0" \
  --poles "0.2,0.3,0.4" \
  --method place \
  --plot none \
  --pretty \
  --save_json \
  --name mimo_place
```

## G) MIMO — `auto` (chooses PLACE for r>1)
```bash
python cli.py \
  --A "0 1 0; 0 0 1; -1.2 -1.3 -0.4" \
  --B "1 0; 0 1; 1 1" \
  --C "1 0 0" \
  --poles "0.2,0.3,0.4" \
  --method auto \
  --plot none \
  --name mimo_auto
```

## H) Deadbeat design (Ogata Ex. 6‑7) — MPL dots
```bash
python cli.py \
  --A "0 1; -0.16 -1" \
  --B "0; 1" \
  --C "1 0" \
  --deadbeat \
  --plot mpl \
  --style dots \
  --pretty \
  --save_json \
  --save_csv \
  --name ex6_7_deadbeat
```

## I) Load A,B,C from JSON (Ogata Ex. 6‑8 style) — MPL dots
*(expects `in/sys_tf.json` with keys A,B,C)*
```bash
python cli.py \
  --json_in in/sys_tf.json \
  --poles "0.5+0.5j,0.5-0.5j" \
  --plot mpl \
  --style dots \
  --pretty \
  --save_json \
  --save_csv \
  --name from_json
```

## J) No plot (CSV+JSON only)
```bash
python cli.py \
  --A "0 1; -0.16 -1" \
  --B "0; 1" \
  --C "1 0" \
  --poles "0.5+0.5j,0.5-0.5j" \
  --plot none \
  --save_json \
  --save_csv \
  --name csv_only
```

## K) Change sample length (N=120)
```bash
python cli.py \
  --A "0 1; -0.16 -1" \
  --B "0; 1" \
  --C "1 0" \
  --poles "0.5+0.5j,0.5-0.5j" \
  --samples 120 \
  --plot mpl \
  --style dots \
  --name long_run
```

## L) Override output directory
```bash
python cli.py \
  --A "0 1; -0.16 -1" \
  --B "0; 1" \
  --C "1 0" \
  --poles "0.5+0.5j,0.5-0.5j" \
  --plot mpl \
  --style dots \
  --name custom_out \
  --outdir ./tmp/poletool_out
```

## M) Pretty OFF (lean logs)
```bash
python cli.py \
  --A "0 1; -0.16 -1" \
  --B "0; 1" \
  --C "1 0" \
  --poles "0.5+0.5j,0.5-0.5j" \
  --plot none \
  --name plain
```

## N) Also runnable via module path (optional)
*(Works from anywhere in the repo if your PYTHONPATH includes the project root.)*
```bash
python -m pole_placement.poleTool.cli \
  --help
```

## O) Generate class diagram (PlantUML .puml)
```bash
python tools/class_diagram.py
```

### Notes
- **Methods:** `auto | ackermann | ogata | eigs | place`
- **Backends:** `mpl | plotly | none` (Plotly writes a `.html` file; MPL writes `.png`)
- **Styles:** `dots | stairs | connected`
- **Deadbeat:** `--deadbeat` places all poles at zero (SISO)
- **Artifacts:** JSON summary (`<name>.json`), step CSV (`<name>_step.csv`), and optional plot under `./out/` (or `--outdir`).

### Sphinx

python -m transient_analysis.hurwitzTool.cli sphinx-skel transient_analysis/hurwitzTool/docs
python -m sphinx -b html docs docs/_build/html
open docs/_build/html/index.html
sphinx-autobuild docs docs/_build/html