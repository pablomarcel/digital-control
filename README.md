# Digital Control

[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-3D74F7.svg)](https://pablomarcel.github.io/control-digitalControl/)
[![Build & Publish Docs](https://github.com/pablomarcel/control-digitalControl/actions/workflows/pages.yml/badge.svg)](https://github.com/pablomarcel/control-digitalControl/actions/workflows/pages.yml)

Digital Control is a Python-based collection of command-line tools for studying, simulating, and designing discrete-time control systems. The project focuses on reproducible engineering workflows inspired by standard digital-control topics, including z-transforms, z-plane analysis, state-space methods, pole placement, observers, Kalman filtering, RST controllers, LQR, Jury stability, zero-order hold behavior, ADC/DAC models, and related digital-system utilities.

The repository is organized as a set of focused packages. Each tool provides a command-line interface, example inputs, repeatable run commands, and file-based outputs so that analyses can be reproduced without relying on notebooks or proprietary desktop software.

## Documentation

Live documentation is available here:

**https://pablomarcel.github.io/control-digitalControl/**

Per-package documentation begins with:

- [intro/adcTool](https://pablomarcel.github.io/control-digitalControl/intro/adcTool)

## Project Goals

Digital Control is intended to serve as a practical study and design environment for discrete-time control systems. The main goals are:

- provide small, testable tools for individual digital-control topics;
- keep workflows reproducible through command-line execution and file-based inputs;
- generate useful engineering artifacts such as JSON, CSV, HTML, PNG, and VCD outputs;
- make textbook-style computations easier to inspect, repeat, and extend;
- support both learning workflows and exploratory design studies.

## Repository Structure

```text
intro/
  adcTool/                # Counter and SAR ADC simulators
  dacTool/                # DAC staircase and quantization models
  demuxTool/              # N-way digital demultiplexer models
  muxTool/                # N-way digital multiplexer models
  vcdTool/                # VCD validation, merge, and summary helpers
  zohTool/                # Zero-order hold and droop models

kalmanFilters/
  kalmanFilterTool/       # Discrete Kalman filtering

polePlacement/
  controllabilityTool/    # Controllability tests, rank checks, and Gramians
  observabilityTool/      # Observability tests and observable canonical form
  observerTool/           # Observer and estimator design workflows
  poleTool/               # Discrete pole-placement methods
  servoTool/              # Integral-action servo design
  transformationTool/     # Canonical-form transformations

polynomialEquations/
  polynomialTool/         # Polynomial and Diophantine-equation workflows

quadraticControl/
  quadraticTool/          # Finite-horizon and steady-state discrete LQR

rstControllers/
  rstTool/                # RST controller synthesis
  rstPlotTool/            # RST response plotting and visualization

stateSpace/
  stateSpaceTool/         # Discrete state-space simulation
  stateConverterTool/     # Transfer-function/state-space conversion and discretization
  stateSolverTool/        # State-transition and response solvers
  liapunovTool/           # Discrete Lyapunov stability analysis

systemDesign/
  frequencyResponseTool/  # Frequency-response design support
  juryTestTool/           # Jury stability analysis
  zGridTool/              # z-plane design grids and overlays

zPlaneAnalysis/
  discreteResponseTool/   # Discrete impulse and step response analysis

zTransform/
  zTransformTool/         # Z-transform, inverse Z-transform, and difference equations
```

Most packages include:

- `cli.py` for command-line execution;
- `apis.py`, `core.py`, `app.py`, `io.py`, or similar modules for structured implementation;
- `in/` for example inputs;
- `out/` for generated outputs;
- `RUNS.md` with copy-paste command examples;
- `tests/` for package-level validation.

## Design Principles

### CLI-first workflow

The tools are designed to be run from the terminal. Important options are exposed as command-line flags, and package-specific examples are documented in `RUNS.md` files.

### Reproducible inputs and outputs

Inputs are stored in package-level `in/` folders. Outputs are written to `out/` folders. This keeps each example easy to rerun, compare, and archive.

### Small packages with focused responsibilities

Each tool targets a specific topic rather than trying to be a monolithic control-systems application. This makes the code easier to test, debug, and extend.

### Open Python stack

The project uses the Python scientific-computing ecosystem, including NumPy, SciPy, SymPy, Matplotlib, Plotly, python-control, PyRTL, and related packages where appropriate.

### Testable engineering calculations

The project emphasizes repeatable numerical workflows. Tests are included at the package level to support refactoring and to protect existing behavior.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/pablomarcel/control-digitalControl.git
cd digitalControl

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run a package-level command:

```bash
cd systemDesign/zGridTool
python cli.py --help
```

Then open the package's `RUNS.md` file for tested example commands.

## Example Workflow

A typical workflow is:

```bash
cd systemDesign/zGridTool
python cli.py --help
# choose a command from RUNS.md
# review generated outputs in out/
```

For tools that support plotting, outputs may include static Matplotlib images or interactive Plotly HTML files. Tools that model digital logic or converter timing may also emit VCD traces.

## Input and Output Conventions

Common conventions across the repository:

```text
in/      example inputs such as JSON, CSV, YAML, or VCD files
out/     generated outputs such as JSON, CSV, PNG, HTML, or VCD files
RUNS.md  reproducible command examples for the package
```

Common output types include:

- JSON result packs for structured numerical output;
- CSV exports for matrices, roots, time histories, and frequency-response data;
- PNG figures for reports and documentation;
- interactive HTML plots for visual inspection;
- VCD files for digital timing traces where applicable.

## Testing

Run tests for an individual tool from the repository root. For example:

```bash
pytest systemDesign/zGridTool/tests \
  --cov \
  --cov-config=systemDesign/zGridTool/.coveragerc \
  --cov-report=term-missing
```

To run all available tests:

```bash
pytest
```

## Development Notes

The repository uses a package-per-tool structure. When adding or modifying a tool:

- keep the command-line interface clear and documented;
- keep example inputs under `in/`;
- write generated files under `out/`;
- update `RUNS.md` with reproducible commands;
- add tests for new solver paths or important behavior changes;
- prefer structured dataclasses or clear schemas for inputs and outputs.

## Documentation Build

The project includes GitHub Pages documentation generated from package-level Sphinx projects. The documentation workflow builds the generated documentation and publishes it to the project Pages site.

Local documentation builds may be run from individual docs folders when needed:

```bash
sphinx-build -b html path/to/docs path/to/docs/_build/html
```

## Requirements

The project is developed against modern Python versions and the scientific Python ecosystem. See `requirements.txt` for pinned dependencies.

Typical dependencies include:

- NumPy
- SciPy
- SymPy
- Matplotlib
- Plotly
- python-control
- PyRTL
- pytest
- Sphinx and Furo for documentation

## Contributing

Contributions are welcome. Good contributions are small, reproducible, and tested.

Before opening a pull request:

- run the relevant package tests;
- update `RUNS.md` if command behavior changed;
- document new CLI flags in `--help` text;
- include or update example inputs when adding solver paths;
- verify that generated outputs are written to the expected `out/` folder.

## License

This project is released under the MIT License. See `LICENSE` for details.

## Acknowledgments

This project is informed by standard digital-control coursework and references, especially K. Ogata's *Discrete-Time Control Systems*, along with the broader Python open-source scientific-computing ecosystem.
