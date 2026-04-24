# README — `rstControllers/rstPlotTool` (Discrete RST step plotting)

This guide assumes you **run commands from inside the package directory**:

```bash
cd digitalControl/rst_controllers/rstPlotTool
```

```bash
python cli.py --help
```

**Inputs:** by convention, place CSVs under `in/` in this package.  
**Outputs:** are always written to `out/` in this package (regardless of where inputs live).

```
inputs:  digitalControl/rstControllers/rstPlotTool/in/
outputs: digitalControl/rstControllers/rstPlotTool/out/
```

> You can also point to CSVs anywhere on disk; `in/` is just the default convention.

---

## Single run (from inside `rstControllers/rstPlotTool/`)

```bash
# 1) Default (both backends, MATLAB-like style)
python cli.py in/rst.csv
```

```bash
# 2) Annotate with a design JSON textbox
python cli.py in/rst.csv --annotate in/rst_design.json
```

```bash
# 3) Matplotlib only + crop x-axis + higher DPI
python cli.py in/rst.csv --backend mpl --kmin 0 --kmax 120 --dpi 200
```

```bash
# 4) Plotly only (interactive HTML)
python cli.py in/rst.csv --backend plotly
```

```bash
# 5a) Use a different style (light)
python cli.py in/rst.csv --backend mpl --style light
```

```bash
# 5b) Use a different style (dark)
python cli.py in/rst.csv --backend mpl --style dark
```

```bash
# 6) Set explicit y-limits (and clip traces to them)
python cli.py in/rst.csv --ylimY 0 1.2 --ylimU 0 0.5 --ylimE -0.1 1.0 --clip
```

```bash
# 7) Custom title
python cli.py in/rst.csv --title "RST Step — Baseline"
```

## Overlays (many CSVs on one figure)

```bash
# 8) Overlay everything in in/ (robust axis limits by default)
python cli.py in/*.csv --overlay
```

```bash
# 9) Overlay with full legend (instead of compact)
python cli.py in/*.csv --overlay --legend full
```

```bash
# 10) Overlay but exclude unstable runs (e.g., ‘alt_*’)
python cli.py in/*.csv --overlay --exclude "alt_*"
```

```bash
# 11) Overlay only a subset
python cli.py in/*.csv --overlay --include "*rst*.csv"
```

```bash
# 12) Overlay with explicit limits + clipping
python cli.py in/*.csv --overlay --ylimY 0 1.2 --ylimU 0 0.6 --ylimE -0.1 1.0 --clip
```

```bash
# 13) Overlay showing full extremes (disable robust limiter)
python cli.py in/*.csv --overlay --robust 1.0
```

```bash
# 14) Overlay, Plotly only
python cli.py in/*.csv --overlay --backend plotly
```

```bash
# 15) Overlay with k-range cropping
python cli.py in/*.csv --overlay --kmin 0 --kmax 200
```

## Per-file rendering (no overlay)

```bash
# 16) Produce one PNG (and HTML) per CSV
python cli.py in/*.csv --no-overlay
```

```bash
# 17) Per-file, matplotlib only, higher DPI
python cli.py in/*.csv --no-overlay --backend mpl --dpi 200
```

---

## Alternative: run from project root using module form

```bash
# From digitalControl/ (note the explicit in/ paths)
python -m rst_controllers.rstPlotTool.cli rst_controllers/rstPlotTool/in/rst.csv
```
