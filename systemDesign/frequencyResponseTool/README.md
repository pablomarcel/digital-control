# systemDesign.frequencyResponseTool — Discrete-Time Frequency-Response Design

Object-oriented refactor of the working `frequency_design.py` into a clean, testable package.

- Topic: **Discrete-Time Control Systems by the Frequency Response Method** (Ogata)
- Features:
  - Bilinear mapping: \( w = \frac{2}{T}\, \frac{z-1}{z+1} \)
  - Lead / Lag / Lag–Lead compensators in w-plane
  - Robust Bode engine (direct complex eval; no python-control)
  - Plotly (responsive HTML/PNG/SVG/PDF) and Matplotlib PNG plots
  - Optional step-response CSV from closed loop
  - Run manifest JSON with file outputs
- I/O conventions (when running **inside** the package directory):
  - Inputs: `./in`
  - Outputs: `./out` (default, configurable via `--out`)

## Layout
```
systemDesign/frequencyResponseTool/
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
    test_smoke_cli.py
    test_core_math.py
  in/
  out/
  README.md
```

## Install (optional dev)
```
pip install -r requirements.txt  # if you keep one; otherwise ensure numpy, scipy, matplotlib, plotly, kaleido
```

## Run — from inside `systemDesign/frequencyResponseTool/`
```bash
# Quick help
python cli.py --help
```

### Manual lead (Ogata 4‑12 style) + both plotters
```bash
python cli.py   --T 0.2   --gz-num "0.01873, 0.01752"   --gz-den "1, -1.8187, 0.8187"   --comp lead --K 1.0 --alpha 0.361 --tau 0.979   --plot matplotlib --save-mpl   --plot plotly --plotly-output html   --out out
```

### Auto design from specs (lead)
```bash
python cli.py   --T 0.2   --gz-num "0.01873, 0.01752"   --gz-den "1, -1.8187, 0.8187"   --comp auto --pm 50 --gm 10 --Kv 2   --plot plotly --plotly-output png   --out out
```

### Manual lag
```bash
python cli.py   --T 0.2   --gz-num "0.01873, 0.01752"   --gz-den "1, -1.8187, 0.8187"   --comp lag --K 1.7 --beta 4.0 --tau 0.5   --plot matplotlib --save-mpl   --out out
```

### Manual lag–lead
```bash
python cli.py   --T 0.2   --gz-num "0.01873, 0.01752"   --gz-den "1, -1.8187, 0.8187"   --comp laglead --K 1.0 --beta 4.0 --tau-lag 0.8 --alpha 0.4 --tau-lead 0.2   --plot plotly --plotly-output html   --out out
```

### Inspect plant only (no compensator), Plotly SVG
```bash
python cli.py   --T 0.2   --gz-num "0.01873, 0.01752"   --gz-den "1, -1.8187, 0.8187"   --comp none   --plot plotly --plotly-output svg   --out out
```

### Save unit-step response CSV
```bash
python cli.py   --T 0.2   --gz-num "0.01873, 0.01752"   --gz-den "1, -1.8187, 0.8187"   --comp lead --K 1.0 --alpha 0.361 --tau 0.979   --step 60   --out out
```

## Module entry (from repo root, if package is importable)
```bash
python -m systemDesign.frequencyResponseTool.cli --help
```
