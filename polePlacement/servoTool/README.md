# polePlacement.servoTool — Servo System Design (Ogata Section 6)

Refactor of a working `servo_design.py` into a clean, testable OOP package.

Run from inside the package:
```bash
cd digitalControl/polePlacement/servoTool
python cli.py --help
```
Or from your repo root:
```bash
python -m polePlacement.servoTool.cli --help
```

## In/Out conventions
- Inputs: `./in/`
- Outputs: `./out/` (default). Bare filenames like `--csv y.csv` land under `./out/y.csv`.
