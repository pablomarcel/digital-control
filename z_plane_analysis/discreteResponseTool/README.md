
# zPlaneAnalysis.discreteResponseTool

Object-oriented refactor of `discrete_response_scipy.py` (v1.4). Testable, modular, scalable.

## Layout

- `app.py` – orchestration class `DiscreteResponseApp`
- `core.py` – numerics & math utilities (pure, testable)
- `design.py` – plotting/export (Matplotlib/Plotly; optional at runtime)
- `apis.py` – dataclasses for typed requests
- `cli.py` – import shim + argparse CLI
- `utils.py` – decorators/utilities (outdir policy, timing)
- `tools/` – extras (e.g., `class_diagram.py` emits a PlantUML file)
- `tests/` – pytest tests

## CLI

```bash
cd digitalControl/z_plane_analysis/discreteResponseTool
python cli.py --help
```
