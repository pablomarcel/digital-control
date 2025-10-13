# Digital Control App — Python CLI-First Study & Design Suite

> **Mission:** learn, reproduce, and *do* digital control systems without MATLAB®/Simulink® — using Python, a modern CLI workflow, and open libraries.

This repo is a collection of focused, test-driven Python packages ("tools") that replicate and extend core workflows from **Ogata, *Discrete-Time Control Systems* (1995)** — plus related topics. Each package ships with a friendly **CLI**, example inputs, and a **RUNS.md** full of copy‑paste commands. No notebooks required, no proprietary stack needed.

<p align="center">
  <em>“do we really need MATLAB® for digital control?”</em>
</p>

---

## Why this exists

- I don’t have a MATLAB® license - and I don't need one.
- Ogata drowns you in matrices, so I had to create a computational tool to provide some relief.
- Python’s ecosystem (NumPy, SciPy, SymPy, python‑control, etc.) can do everything the textbooks require — but it’s code-heavy.
- So I wrapped the hard parts into clean **command‑line tools** with consistent I/O, file conventions, and tests.
- The result is a **drop‑in study companion** and **reproducible design lab** for digital control.

---

## What’s inside (exhibits)

[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-3D74F7.svg)](https://pablomarcel.github.io/control-digitalControl/)
[![Build & Publish Docs](https://github.com/pablomarcel/control-digitalControl/actions/workflows/pages.yml/badge.svg)](https://github.com/pablomarcel/control-digitalControl/actions/workflows/pages.yml)

## Documentation

Live docs: **https://pablomarcel.github.io/control-digitalControl/**

Per-package quick links:
- [intro/adcTool](https://pablomarcel.github.io/control-digitalControl/intro/adcTool)

Each subfolder is a cohesive package with its own CLI, tests, and a RUNS.md:

```
intro/
  adcTool/                # Counter & SAR ADC simulators
  dacTool/                # DAC staircases & quantization models
  demuxTool/              # N‑way digital demultiplexer (PyRTL)
  muxTool/                # N‑way digital multiplexer (PyRTL)
  vcdTool/                # VCD helpers: validate/merge/summarize
  zohTool/                # Zero‑order hold & droop models

kalmanFilters/
  kalmanFilterTool/       # Discrete Kalman filtering: steady‑state; time‑varying

polePlacement/
  controllabilityTool/    # Controllability tests (rank/Gramian), CCF
  observabilityTool/      # Observability tests & OCF transforms
  observerTool/           # Luenberger/Kalman observers, pole placement
  poleTool/               # Discrete pole placement (deadbeat/Ackermann)
  servoTool/              # Integral‑action servo design (augmented)
  transformationTool/     # Canonical‑form transforms (CCF/OCF)

polynomialEquations/
  polynomialTool/         # Diophantine/RST synthesis & solvers

quadraticControl/
  quadraticTool/          # Finite‑/steady‑state LQR (discrete)

rstControllers/
  rstTool/                # RST controller synthesis (Diophantine)
  rstPlotTool/            # Response plots for designed RST

stateSpace/
  stateSpaceTool/         # Solve x[k+1]=Ax+Bu; y=Cx
  stateConverterTool/     # TF↔SS, discretization, pulse TF matrix
  stateSolverTool/        # Leverrier, Φ(k) solver, step/impulse
  liapunovTool/           # Discrete Lyapunov stability analysis

systemDesign/
  frequencyResponseTool/  # w‑plane design: Bode + lead/lag
  juryTestTool/           # Jury stability table & margins
  zGridTool/              # z‑plane overlays: ζ, ω_n, ω_d, T_s

zPlaneAnalysis/
  discreteResponseTool/   # Unit‑step/impulse responses; overlays

zTransform/
  zTransformTool/         # Z / inverse‑Z, properties, difference eqs
```

> Each folder includes a **`RUNS.md`** with *single‑command* examples to run **from inside that package**. Most tools accept JSON/CSV/YAML inputs and write results to `out/` (CSV/JSON/HTML/PNG/VCD).

---

## Design philosophy

- **CLI‑first**: Everything important is a flag, not hidden in a notebook cell.
- **Reproducible**: Inputs live in `in/`, outputs in `out/`, commands in `RUNS.md`.
- **Test‑driven**: `pytest` suites for each tool; coverage reports during refactors.
- **Pragmatic math**: Uses python‑control where helpful, but falls back to explicit numerics when necessary for robustness/clarity.
- **Teacher‑friendly**: Plots (Matplotlib and Plotly), CSV/JSON exports, and clean logs you can paste into lectures/reports.

---

## Quick start

```bash
# 1) Clone and create a virtual env (example)
git clone https://github.com/pablomarcel/control-digitalControl.git
cd digitalControl
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) Install dependencies
pip install -U pip
pip install -r requirements.txt

# 3) Run a demo from *inside* a package
cd systemDesign/zGridTool
python cli.py --help
# See RUNS.md for copy‑pasteable commands per package

# 4) Run tests (per tool)
cd ../../
pytest systemDesign/zGridTool/tests --cov --cov-config=systemDesign/zGridTool/.coveragerc --cov-report=term-missing
```

> The repo uses a **consistent import shim** in each package so that `python cli.py ...` works when you `cd` into that folder.

---

## I/O conventions

- **Inputs**: `in/` (e.g., JSON/CSV/YAML/VCD)
- **Outputs**: `out/` (CSV / JSON manifests / PNG / HTML / VCD)
- **Logs**: human‑readable console logs; many CLIs support `--pretty` and `--save_json/--save_csv`

Common capabilities across tools:
- print numeric results to console
- export matrices, roots, responses to **CSV/JSON**
- write **Plotly** interactive HTML and **Matplotlib** PNGs
- write **VCD** traces where it makes sense (e.g., converters, mux/demux)

---

## Example: z‑Grid overlay (systemDesign/zGridTool)

```bash
cd systemDesign/zGridTool
python cli.py --help
# …then pick a command from RUNS.md to overlay poles/zeros and export an interactive Plotly HTML
```

---

## Tested setup

- Python 3.13 (also works with 3.11/3.12 in most tools)
- NumPy 2.x, SciPy 1.15.x, SymPy 1.13.x, matplotlib 3.10.x, plotly 5.x
- macOS 13.7, Windows 10/11 (CLI + plots)
- Continuous refactors with `pytest` suites per tool

See `requirements.txt` for exact pins.

---

## Contributing

Issues and PRs are welcome:
- Respect the folder structure and the **CLI‑first** approach.
- Keep inputs in `in/`, outputs in `out/`, and runnable **RUNS.md** examples.
- Add or update **tests** with any new feature or refactor.
- Prefer small, focused modules and clean dataclasses for I/O (`apis.py`).

A simple PR checklist:
- [ ] `pytest` passes locally for the changed tool(s)
- [ ] `RUNS.md` updated with new/changed commands
- [ ] New flags documented in `cli.py --help`
- [ ] Outputs reproducible under `out/`

---

## License

This project is released under the **MIT License** (see `LICENSE`).

---

## Acknowledgments

- K. Ogata, *Discrete-Time Control Systems* (1995)
- The Python open-source ecosystem: NumPy, SciPy, SymPy, matplotlib, plotly, python‑control, and many others.

---

