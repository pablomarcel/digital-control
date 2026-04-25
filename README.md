# Digital Control

[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-3D74F7.svg)](https://pablomarcel.github.io/control-digitalControl/)
[![Build & Publish Docs](https://github.com/pablomarcel/control-digitalControl/actions/workflows/pages.yml/badge.svg)](https://github.com/pablomarcel/control-digitalControl/actions/workflows/pages.yml)

**Digital Control** is a Python-first engineering toolkit for studying, simulating, and designing discrete-time control systems through reproducible command-line workflows. It collects focused tools for z-transforms, z-plane analysis, sampled-data behavior, state-space simulation, pole placement, observers, Kalman filtering, RST control, LQR, Jury stability, ADC/DAC modeling, VCD utilities, and supporting digital-system analysis.

The project is organized as a set of small, topic-specific packages instead of a single monolithic application. Each package is intended to be inspectable, testable, and repeatable: inputs live in files, commands are documented, and generated artifacts are written to package-level output folders. The result is a practical environment for learning, verification, and exploratory control-system design without depending on notebooks or proprietary desktop tools.

## Documentation

Live documentation is published with GitHub Pages:

**https://pablomarcel.github.io/control-digitalControl/**

Package documentation starts here:

- [intro/adcTool](https://pablomarcel.github.io/control-digitalControl/intro/adcTool)

## What This Repository Provides

Digital Control is built around repeatable engineering workflows. The repository is designed to help users:

- analyze discrete-time systems from transfer-function, polynomial, and state-space viewpoints;
- simulate sampled-data behavior, digital responses, converters, timing traces, and controller behavior;
- design and inspect control structures such as pole-placement controllers, observers, RST controllers, Kalman filters, servo systems, and LQR regulators;
- generate structured outputs for review, documentation, regression testing, and future automation;
- keep examples reproducible through command-line execution, package-level `RUNS.md` files, and file-based input/output conventions.

## Repository Layout

```text
intro/
  adcTool/                # Counter and SAR ADC simulators
  dacTool/                # DAC staircase and quantization models
  demuxTool/              # N-way digital demultiplexer models
  muxTool/                # N-way digital multiplexer models
  vcdTool/                # VCD validation, merge, and summary utilities
  zohTool/                # Zero-order hold and droop models

kalmanFilters/
  kalmanFilterTool/       # Discrete Kalman filtering workflows

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
  discreteResponseTool/   # Discrete impulse and step-response analysis

zTransform/
  zTransformTool/         # Z-transform, inverse Z-transform, and difference equations
```

Most tools follow the same package pattern:

```text
cli.py        command-line entry point
apis.py       public-facing solver/API layer, when applicable
app.py        orchestration layer, when applicable
core.py       numerical methods and domain logic
io.py         file loading, validation, and output writing
in/           example input files
out/          generated results
RUNS.md       tested copy-paste command examples
tests/        package-level regression tests
```

The exact module names vary by package, but the intent is consistent: keep solver logic separated from command-line parsing, keep examples close to the tool that uses them, and keep generated outputs easy to inspect.

## Design Philosophy

### CLI-first engineering workflow

The repository is optimized for terminal-driven work. A typical tool exposes its main behavior through `cli.py`, with examples documented in its package-level `RUNS.md`. This makes each analysis easy to rerun, compare, script, and capture in version control.

### Reproducible inputs and outputs

Examples are stored under `in/` folders and generated artifacts are written to `out/` folders. This convention keeps the workflow explicit: the input file defines the problem, the command defines the execution path, and the output files capture the result.

### Focused packages instead of a monolith

Each package addresses a specific digital-control topic. This keeps implementations smaller, easier to reason about, and easier to extend without breaking unrelated tools.

### Structured numerical artifacts

Outputs are designed to be useful beyond the terminal. Depending on the package, generated artifacts may include JSON result packs, CSV data exports, PNG plots, interactive HTML visualizations, and VCD timing traces.

### Open Python ecosystem

The project builds on the scientific Python stack where appropriate, including NumPy, SciPy, SymPy, Matplotlib, Plotly, python-control, PyRTL, pytest, Sphinx, and Furo.

### Testable calculations

The repository treats numerical behavior as something that should be checked, not guessed. Package-level tests support refactoring, protect existing behavior, and provide confidence that examples remain reproducible as tools evolve.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/pablomarcel/control-digitalControl.git
cd control-digitalControl

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

Then open that package's `RUNS.md` file for tested example commands.

## Typical Workflow

A normal package workflow looks like this:

```bash
cd systemDesign/zGridTool
python cli.py --help
# choose a tested command from RUNS.md
# run the example
# review generated files in out/
```

For packages with plotting support, outputs may include static Matplotlib figures or interactive Plotly HTML files. Tools that model digital timing behavior may also emit VCD traces for inspection in waveform viewers.

## Input and Output Conventions

Common package-level conventions:

```text
in/      input files such as JSON, CSV, YAML, TXT, or VCD
out/     generated outputs such as JSON, CSV, PNG, HTML, or VCD
RUNS.md  tested command examples for the package
```

Common output types:

- **JSON** result packs for structured numerical output;
- **CSV** exports for matrices, roots, time histories, frequency-response data, or tabular summaries;
- **PNG** figures for documentation and reports;
- **HTML** files for interactive visual inspection;
- **VCD** files for digital timing traces and waveform analysis.

## Testing

Run all available tests from the repository root:

```bash
pytest
```

Run tests for an individual package:

```bash
pytest systemDesign/zGridTool/tests \
  --cov \
  --cov-config=systemDesign/zGridTool/.coveragerc \
  --cov-report=term-missing
```

Because this repository is organized as independent tools, package-level testing is especially useful when modifying a solver, adding a command, or changing output formatting.

## Documentation Build

The repository includes Sphinx-based documentation published through GitHub Pages. Local documentation builds may be run from the relevant documentation folder:

```bash
sphinx-build -b html path/to/docs path/to/docs/_build/html
```

When updating a package, keep its CLI help, examples, and documentation aligned so that command behavior remains discoverable.

## Development Guidelines

When adding or modifying a tool:

- keep command-line behavior clear and documented;
- preserve the package-level `in/`, `out/`, and `RUNS.md` workflow;
- keep numerical logic in dedicated solver/core modules rather than burying it in CLI code;
- add or update example inputs for new solver paths;
- write tests for new calculations, edge cases, and regression-sensitive behavior;
- prefer structured outputs that can be inspected programmatically;
- avoid hidden state and make file paths explicit;
- update documentation when flags, examples, or output conventions change.

## Requirements

See `requirements.txt` for the project dependency set. Typical dependencies include:

- NumPy
- SciPy
- SymPy
- Matplotlib
- Plotly
- python-control
- PyRTL
- pytest
- Sphinx
- Furo

## Contributing

Contributions are welcome when they are focused, reproducible, and tested. A strong contribution should include the relevant input examples, updated command documentation, and tests that demonstrate the expected behavior.

Before opening a pull request:

- run the affected package tests;
- run broader tests when shared utilities are modified;
- update `RUNS.md` if command behavior changed;
- document new CLI flags in `--help` text;
- include or update example input files when adding solver paths;
- verify that generated files are written to the expected `out/` folder.

## License

This project is released under the MIT License. See `LICENSE` for details.

## Acknowledgments

This project is informed by standard digital-control coursework and references, especially K. Ogata's *Discrete-Time Control Systems*, and by the broader Python scientific-computing ecosystem.
