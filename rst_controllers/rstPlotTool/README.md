# README — `rstControllers.rstPlotTool` (Discrete RST step plotting)

Run from your project root (e.g., `.../digitalControl/`). Defaults:
- Inputs: wherever your CSVs live (for example, your RST runs may write into `rstControllers/rstPlotTool/out/`).
- Outputs: `rstControllers/rstPlotTool/out/`

## CLI
```bash
python -m rst_controllers.rstPlotTool.cli --help
# or from inside the package directory
python rst_controllers/rstPlotTool/cli.py --help
```

## Single run
```bash
# 1) Default (both backends, MATLAB-like style)
python rst_controllers/rstPlotTool/cli.py rst_controllers/rstPlotTool/out/rst.csv

# 2) Annotate with a design JSON textbox
python rst_controllers/rstPlotTool/cli.py rst_controllers/rstPlotTool/out/rst.csv --annotate rst_controllers/rstPlotTool/out/rst_design.json

# 3) Matplotlib only + crop x-axis + higher DPI
python rst_controllers/rstPlotTool/cli.py rst_controllers/rstPlotTool/out/rst.csv --backend mpl --kmin 0 --kmax 120 --dpi 200

# 4) Plotly only (interactive HTML)
python rst_controllers/rstPlotTool/cli.py rst_controllers/rstPlotTool/out/rst.csv --backend plotly

# 5) Use a different style (light or dark)
python rst_controllers/rstPlotTool/cli.py rst_controllers/rstPlotTool/out/rst.csv --backend mpl --style light
python rst_controllers/rstPlotTool/cli.py rst_controllers/rstPlotTool/out/rst.csv --backend mpl --style dark

# 6) Set explicit y-limits (and clip traces to them)
python rst_controllers/rstPlotTool/cli.py rst_controllers/rstPlotTool/out/rst.csv --ylimY 0 1.2 --ylimU 0 0.5 --ylimE -0.1 1.0 --clip

# 7) Custom title
python rst_controllers/rstPlotTool/cli.py rst_controllers/rstPlotTool/out/rst.csv --title "RST Step — Baseline"
```

## Overlays (many CSVs on one figure)
```bash
# 8) Overlay everything in out/ (robust axis limits by default)
python -m rst_controllers.rstPlotTool.cli rst_controllers/rstPlotTool/out/*.csv --overlay

# 9) Overlay with full legend (instead of compact)
python -m rst_controllers.rstPlotTool.cli rst_controllers/rstPlotTool/out/*.csv --overlay --legend full

# 10) Overlay but exclude unstable runs (e.g., ‘alt_*’)
python -m rst_controllers.rstPlotTool.cli rst_controllers/rstPlotTool/out/*.csv --overlay --exclude "alt_*"

# 11) Overlay only a subset
python -m rst_controllers.rstPlotTool.cli rst_controllers/rstPlotTool/out/*.csv --overlay --include "*rst*.csv"

# 12) Overlay with explicit limits + clipping
python -m rst_controllers.rstPlotTool.cli rst_controllers/rstPlotTool/out/*.csv --overlay --ylimY 0 1.2 --ylimU 0 0.6 --ylimE -0.1 1.0 --clip

# 13) Overlay showing full extremes (disable robust limiter)
python -m rst_controllers.rstPlotTool.cli rst_controllers/rstPlotTool/out/*.csv --overlay --robust 1.0

# 14) Overlay, Plotly only
python -m rst_controllers.rstPlotTool.cli rst_controllers/rstPlotTool/out/*.csv --overlay --backend plotly

# 15) Overlay with k-range cropping
python -m rst_controllers.rstPlotTool.cli rst_controllers/rstPlotTool/out/*.csv --overlay --kmin 0 --kmax 200
```

## Per-file rendering (no overlay)
```bash
# 16) Produce one PNG (and HTML) per CSV
python -m rst_controllers.rstPlotTool.cli rst_controllers/rstPlotTool/out/*.csv --no-overlay

# 17) Per-file, matplotlib only, higher DPI
python -m rst_controllers.rstPlotTool.cli rst_controllers/rstPlotTool/out/*.csv --no-overlay --backend mpl --dpi 200
```
