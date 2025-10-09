# quadraticControl.quadraticTool — RUNS.md

Run these **from inside** the package directory:

```bash
cd quadraticControl/quadraticTool
```

```bash
python cli.py --help   # single subcommand: solve
```
Outputs are written under `quadraticControl/quadraticTool/out/<name>/` unless `--outdir` is given.

---

## Modes supported (via YAML config)
- `fh-dt` — Finite-horizon DT LQR
- `ct-siso-ogata` — CT→DT SISO weights (Ogata Ex. 8‑2), then finite-horizon solve
- `ss-lqr` — Steady-state DT LQR (DARE)
- `servo-lqr` — Servo LQR (integral augmentation)
- `lyap` — Discrete Lyapunov (G' P G − P = −Q), optional J(x₀)
- `lyap-sweep` — Parameter sweep for Lyapunov J (handles unstable/unsolved points gracefully)

> Most examples below accept `--plot mpl` or `--plot plotly` (or omit to disable plotting).

---

## A) Ogata Ex. 8-1 — Finite-horizon DT (no cross-term)
**YAML:** `in/ex8_1.yaml`
```bash
python cli.py solve --infile in/ex8_1.yaml --name ex8_1 --plot mpl
# Plotly variant:
python cli.py solve --infile in/ex8_1.yaml --name ex8_1_plotly --plot plotly
# Headless (no plots):
python cli.py solve --infile in/ex8_1.yaml --name ex8_1_noplot
```

## B) Ogata Ex. 8-2 — CT→DT SISO with cross-term, then FH solve
**YAML:** `in/ex8_2.yaml`
```bash
python cli.py solve --infile in/ex8_2.yaml --name ex8_2 --plot mpl
# Plotly variant:
python cli.py solve --infile in/ex8_2.yaml --name ex8_2_plotly --plot plotly
```

## C) Ogata Ex. 8-3 — Lyapunov J(a) at fixed a
**YAML:** `in/ex8_3.yaml`
```bash
python cli.py solve --infile in/ex8_3.yaml --name ex8_3_a_-0p25
# Headless:
python cli.py solve --infile in/ex8_3.yaml --name ex8_3_a_-0p25_noplot
```

## D) Ogata Ex. 8-3 — sweep a to find a*
**YAML:** `in/ex8_3_sweep.yaml`
```bash
python cli.py solve --infile in/ex8_3_sweep.yaml --name ex8_3_sweep --plot mpl
# Plotly variant:
python cli.py solve --infile in/ex8_3_sweep.yaml --name ex8_3_sweep_plotly --plot plotly
```
**Notes:**
- The sweep writes `<param>_grid.csv` and `J.csv` for all points.
- If no valid/stable point exists, `P_star.csv` is omitted and the summary shows `None` for `a*` / `J_min`.

## E) Ogata Ex. 8-4 — Steady-state LQR (DARE)
**YAML:** `in/ex8_4.yaml`
```bash
python cli.py solve --infile in/ex8_4.yaml --name ex8_4
```

## F) Servo LQR — augmented integrator (SISO)
**YAML:** `in/servo.yaml`
```bash
python cli.py solve --infile in/servo.yaml --name servo --plot mpl
# Plotly variant:
python cli.py solve --infile in/servo.yaml --name servo_plotly --plot plotly
```

---

## G) General options & tips
- `--outdir <dir>` — write case folder under a custom directory instead of the default `out/`.
  ```bash
  python cli.py solve --infile in/ex8_1.yaml --name ex8_1_custom --outdir ./quadratic_out --plot mpl
  ```
- Plots:
  - `--plot mpl` saves a PNG next to CSVs.
  - `--plot plotly` saves an interactive HTML.
  - Omit `--plot` for headless runs (CSV + summary only).
- Outputs (typical):
  - `summary.txt` — human-readable summary for the run
  - Controller/analysis CSV/Mat files depending on mode, e.g.
    - `K.csv`, `P0.csv`/`P.csv`, `x.csv`, `u.csv` (finite-horizon)
    - `P.csv`, `K.csv` (steady-state LQR)
    - `y.csv`, `u.csv`, `x1.csv`, `x2.csv` (servo sim traces)
    - `P.csv` and optional `J` (Lyapunov)
    - `<param>_grid.csv`, `J.csv`, optional `P_star.csv` (Lyapunov sweep)

> Advanced overrides (e.g., parameter substitution/sweep overrides) are supported in the app layer.
> If/when those flags are exposed via the CLI, you can pass `--param k=v` (multiple times) and
> `--sweep name=start:stop:points`. For now, the provided YAMLs cover the typical flows.
