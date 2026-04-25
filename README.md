# Digital Control

[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-3D74F7.svg)](https://pablomarcel.github.io/digital-control/)
[![Build & Publish Docs](https://github.com/pablomarcel/digital-control/actions/workflows/pages.yml/badge.svg)](https://github.com/pablomarcel/digital-control/actions/workflows/pages.yml)
[![Python](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Digital Control** is a Python-first engineering toolkit for studying, simulating, and designing discrete-time control systems through reproducible command-line workflows. It collects focused tools for z-transforms, z-plane analysis, sampled-data behavior, state-space simulation, pole placement, observers, Kalman filtering, RST control, LQR, Jury stability, ADC/DAC modeling, VCD utilities, and supporting digital-system analysis.

The project is organized as a set of small, topic-specific packages instead of a single monolithic application. Each package is intended to be inspectable, testable, and repeatable: inputs live in files, commands are documented, and generated artifacts are written to package-level output folders. The result is a practical environment for learning, verification, and exploratory control-system design without depending on notebooks or proprietary desktop tools.

## Documentation

Live documentation is published with GitHub Pages:

**https://pablomarcel.github.io/digital-control/**

### Package Documentation Index

| Area | Tool | Documentation |
|---|---|---|
| Introduction | ADC Tool | [introduction/adcTool](https://pablomarcel.github.io/digital-control/introduction/adcTool/) |
| Introduction | DAC Tool | [introduction/dacTool](https://pablomarcel.github.io/digital-control/introduction/dacTool/) |
| Introduction | DEMUX Tool | [introduction/demuxTool](https://pablomarcel.github.io/digital-control/introduction/demuxTool/) |
| Introduction | MUX Tool | [introduction/muxTool](https://pablomarcel.github.io/digital-control/introduction/muxTool/) |
| Introduction | VCD Tool | [introduction/vcdTool](https://pablomarcel.github.io/digital-control/introduction/vcdTool/) |
| Introduction | ZOH Tool | [introduction/zohTool](https://pablomarcel.github.io/digital-control/introduction/zohTool/) |
| Kalman Filters | Kalman Filter Tool | [kalman_filters/kalmanFilterTool](https://pablomarcel.github.io/digital-control/kalman_filters/kalmanFilterTool/) |
| Pole Placement | Controllability Tool | [pole_placement/controllabilityTool](https://pablomarcel.github.io/digital-control/pole_placement/controllabilityTool/) |
| Pole Placement | Observability Tool | [pole_placement/observabilityTool](https://pablomarcel.github.io/digital-control/pole_placement/observabilityTool/) |
| Pole Placement | Observer Tool | [pole_placement/observerTool](https://pablomarcel.github.io/digital-control/pole_placement/observerTool/) |
| Pole Placement | Pole Tool | [pole_placement/poleTool](https://pablomarcel.github.io/digital-control/pole_placement/poleTool/) |
| Pole Placement | Servo Tool | [pole_placement/servoTool](https://pablomarcel.github.io/digital-control/pole_placement/servoTool/) |
| Pole Placement | Transformation Tool | [pole_placement/transformationTool](https://pablomarcel.github.io/digital-control/pole_placement/transformationTool/) |
| Polynomial Equations | Polynomial Tool | [polynomial_equations/polynomialTool](https://pablomarcel.github.io/digital-control/polynomial_equations/polynomialTool/) |
| Quadratic Control | Quadratic Tool | [quadratic_control/quadraticTool](https://pablomarcel.github.io/digital-control/quadratic_control/quadraticTool/) |
| RST Controllers | RST Plot Tool | [rst_controllers/rstPlotTool](https://pablomarcel.github.io/digital-control/rst_controllers/rstPlotTool/) |
| RST Controllers | RST Tool | [rst_controllers/rstTool](https://pablomarcel.github.io/digital-control/rst_controllers/rstTool/) |
| State Space | Liapunov Tool | [state_space/liapunovTool](https://pablomarcel.github.io/digital-control/state_space/liapunovTool/) |
| State Space | State Converter Tool | [state_space/stateConverterTool](https://pablomarcel.github.io/digital-control/state_space/stateConverterTool/) |
| State Space | State Solver Tool | [state_space/stateSolverTool](https://pablomarcel.github.io/digital-control/state_space/stateSolverTool/) |
| State Space | State Space Tool | [state_space/stateSpaceTool](https://pablomarcel.github.io/digital-control/state_space/stateSpaceTool/) |
| System Design | Frequency Response Tool | [system_design/frequencyResponseTool](https://pablomarcel.github.io/digital-control/system_design/frequencyResponseTool/) |
| System Design | Jury Test Tool | [system_design/juryTestTool](https://pablomarcel.github.io/digital-control/system_design/juryTestTool/) |
| System Design | Z-Grid Tool | [system_design/zGridTool](https://pablomarcel.github.io/digital-control/system_design/zGridTool/) |
| Z-Plane Analysis | Discrete Response Tool | [z_plane_analysis/discreteResponseTool](https://pablomarcel.github.io/digital-control/z_plane_analysis/discreteResponseTool/) |
| Z-Transform | Z-Transform Tool | [z_transform/zTransformTool](https://pablomarcel.github.io/digital-control/z_transform/zTransformTool/) |

## What This Repository Provides

Digital Control is built around repeatable engineering workflows. The repository is designed to help users:

- analyze discrete-time systems from transfer-function, polynomial, z-plane, and state-space viewpoints;
- simulate sampled-data behavior, digital responses, converters, timing traces, and controller behavior;
- design and inspect control structures such as pole-placement controllers, observers, RST controllers, Kalman filters, servo systems, and LQR regulators;
- generate structured outputs for review, documentation, regression testing, and future automation;
- keep examples reproducible through command-line execution, package-level `RUNS.md` files, and file-based input/output conventions.

## Repository Layout

```text
introduction/
  adcTool/                # Counter and SAR ADC simulators
  dacTool/                # DAC staircase and quantization models
  demuxTool/              # N-way digital demultiplexer models
  muxTool/                # N-way digital multiplexer models
  vcdTool/                # VCD validation, merge, and summary utilities
  zohTool/                # Zero-order hold and droop models

kalman_filters/
  kalmanFilterTool/       # Discrete Kalman filtering workflows

pole_placement/
  controllabilityTool/    # Controllability tests, rank checks, and Gramians
  observabilityTool/      # Observability tests and observable canonical form
  observerTool/           # Observer and estimator design workflows
  poleTool/               # Discrete pole-placement methods
  servoTool/              # Integral-action servo design
  transformationTool/     # Canonical-form transformations

polynomial_equations/
  polynomialTool/         # Polynomial and Diophantine-equation workflows

quadratic_control/
  quadraticTool/          # Finite-horizon and steady-state discrete LQR

rst_controllers/
  rstPlotTool/            # RST response plotting and visualization
  rstTool/                # RST controller synthesis

state_space/
  liapunovTool/           # Discrete Lyapunov stability analysis
  stateConverterTool/     # Transfer-function/state-space conversion and discretization
  stateSolverTool/        # State-transition and response solvers
  stateSpaceTool/         # Discrete state-space simulation

system_design/
  frequencyResponseTool/  # Frequency-response design support
  juryTestTool/           # Jury stability analysis
  zGridTool/              # z-plane design grids and overlays

z_plane_analysis/
  discreteResponseTool/   # Discrete impulse and step-response analysis

z_transform/
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

## Tool Families

### Introductory digital-system tools

The `introduction/` packages cover foundational sampled-data and digital-interface concepts: ADC behavior, DAC staircase output, multiplexing and demultiplexing, zero-order hold behavior, and VCD timing-file workflows. These tools are useful for connecting control-system theory to the practical digital signals that feed and actuate real systems.

### Z-transform and z-plane analysis

The `z_transform/` and `z_plane_analysis/` packages support symbolic and numerical workflows around z-transforms, inverse z-transforms, difference equations, impulse response, step response, pole-zero visualization, and response analysis.

### State-space workflows

The `state_space/` packages cover simulation, state-transition solutions, transfer-function/state-space conversion, discretization, and discrete Lyapunov stability analysis. They are intended to make state-space calculations inspectable from the command line rather than hidden inside notebooks.

### Pole placement, observers, and servo design

The `pole_placement/` packages collect design and verification workflows for controllability, observability, canonical transformations, pole placement, observer construction, and integral-action servo design.

### RST, LQR, Kalman, and system design

The RST, quadratic-control, Kalman-filter, and system-design packages cover higher-level controller workflows: RST synthesis, response plotting, discrete LQR, Kalman filtering, Jury stability, frequency-response design, and z-grid design overlays.

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
git clone https://github.com/pablomarcel/digital-control.git
cd digital-control

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run a package-level command:

```bash
cd system_design/zGridTool
python cli.py --help
```

Then open that package's `RUNS.md` file for tested example commands.

## Typical Workflow

A normal package workflow looks like this:

```bash
cd system_design/zGridTool
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
pytest system_design/zGridTool/tests \
  --cov \
  --cov-config=system_design/zGridTool/.coveragerc \
  --cov-report=term-missing
```

Because this repository is organized as independent tools, package-level testing is especially useful when modifying a solver, adding a command, or changing output formatting.

## Documentation Build

The repository includes Sphinx-based documentation published through GitHub Pages. Local documentation builds may be run from the relevant documentation folder:

```bash
sphinx-build -b html path/to/docs path/to/docs/_build/html
```

Several package CLIs include a `sphinx-skel` helper that creates a conservative documentation skeleton with Sphinx-safe `.rst` files, `_static/.gitkeep`, `_templates/.gitkeep`, a minimal `Makefile`, and module discovery that only documents importable modules.

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
- update documentation when flags, examples, or output conventions change;
- keep docstrings conservative enough for Sphinx autodoc and docutils.

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
- verify that generated files are written to the expected `out/` folder;
- verify the relevant documentation page still builds and resolves under `https://pablomarcel.github.io/digital-control/`.

## License

This project is released under the MIT License. See `LICENSE` for details.

## Acknowledgments

This project is informed by standard digital-control coursework and references, especially K. Ogata's *Discrete-Time Control Systems*, and by the broader Python scientific-computing ecosystem.
