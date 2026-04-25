# kalmanFilters.kalmanFilterTool — OOP Kalman Filter Tool

You can run this tool **from inside this folder** (preferred for per-package docs),
or from the **project root**. Defaults for I/O adjust accordingly.

## Run from inside `kalmanFilters/kalmanFilterTool/`
> Outputs go to `./out/` unless a path is provided.

### Quick help
```bash
python cli.py \
  --help
```

### 1) Time-varying KF (CV model) — CSV + PNG + HTML
```bash
python cli.py \
  --dt 0.05 \
  --T 10 \
  --q 0.25 \
  --r 4.0 \
  --backend both \
  --save_csv kf_cv.csv \
  --save_png kf_cv.png \
  --save_html kf_cv.html
```

### 2) Steady-state KF (DARE)
```bash
python cli.py \
  --dt 0.05 \
  --T 10 \
  --q 0.1 \
  --r 9.0 \
  --steady \
  --backend mpl \
  --save_png kf_cv_ss.png
```

### 3) Custom model override (row G auto-transposed) — CSV only
```bash
python cli.py \
  --A "1 0.05; 0 1" \
  --B "0.00125; 0.05" \
  --C "1 0" \
  --G "0 1" \
  --Q "0.01 0; 0 0.1" \
  --R "4" \
  --backend none \
  --save_csv kf_custom.csv
```

### 4) Generate a PlantUML class diagram file
```bash
python tools/class_diagram.py \
  --out out
```

## Alternatively: run from project root
> Outputs go to `kalmanFilters/kalmanFilterTool/out/` by default.

```bash
python -m kalman_filters.kalmanFilterTool.cli \
  --help
```

```bash
python -m kalman_filters.kalmanFilterTool.cli \
  --dt 0.05 \
  --T 10 \
  --q 0.25 \
  --r 4.0 \
  --backend both \
  --save_csv kf_cv.csv \
  --save_png kf_cv.png \
  --save_html kf_cv.html
```

### Sphinx

python -m kalman_filters.kalmanFilterTool.cli sphinx-skel kalman_filters/kalmanFilterTool/docs
python -m sphinx -b html docs docs/_build/html
open docs/_build/html/index.html
sphinx-autobuild docs docs/_build/html