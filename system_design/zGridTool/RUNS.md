# systemDesign.zGridTool — RUNS.md (Expanded)

Run from inside the package:
```bash
cd digitalControl/system_design/zGridTool
```

```bash
python cli.py \
  --help
```

All **inputs** are read from `in/` (unless you pass absolute paths).  
All **outputs** are written to `out/` (unless you pass absolute paths).

## A) Matplotlib (PNG) — basics

1) Basic grid (Nyquist half)
```bash
python cli.py \
  --T 0.05 \
  --backend mpl \
  --png zgrid_basic.png
```

2) Full 0..2π spirals, dark mode
```bash
python cli.py \
  --T 0.05 \
  --theta_max 6.283185307179586 \
  --dark \
  --backend mpl \
  --png zgrid_full_dark.png
```

3) Custom ζ, rays, and ωnT
```bash
python cli.py \
  --T 0.05 \
  --backend mpl \
  --zetas 0.2 0.3 0.5 0.7 0.9 \
  --wd_over_ws 0 0.125 0.25 0.333 0.5 \
  --wnT 0.4 0.8 1.2 1.6 2.0 \
  --png zgrid_custom.png
```

4) Settling-time disk (σ₁ = 1.5) ⇒ |z| ≤ e^{-σ₁ T}
```bash
python cli.py \
  --T 0.1 \
  --settling_sigma 1.5 \
  --backend mpl \
  --png zgrid_settling.png
```

5) Export all grid curves to CSV (rings, ζ-spirals, ωnT curves, rays)
```bash
python cli.py \
  --T 0.05 \
  --backend mpl \
  --export_csv_prefix zgrid_curves \
  --png zgrid_export.png
```
This writes (under `out/`):
- `zgrid_curves_zeta_*.csv`, `zgrid_curves_wnT_*.csv`
- `zgrid_curves_rays.csv`
- `zgrid_curves_settling.csv` (if `--settling_sigma` provided)

## B) Plotly (HTML) — “polish” runs

1) Responsive, compact title, minimal legend at bottom (default)
```bash
python cli.py \
  --T 0.05 \
  --backend plotly \
  --plotly zgrid.html \
  --png zgrid_plotly.png
```

2) Full legend with legend on the right
```bash
python cli.py \
  --T 0.05 \
  --backend plotly \
  --legend_mode full \
  --legend_loc right \
  --plotly zgrid_fulllegend_right.html
```

3) Dark theme + inside legend (bottom-right overlay)
```bash
python cli.py \
  --T 0.05 \
  --backend plotly \
  --theme plotly_dark \
  --legend_loc inside \
  --plotly zgrid_dark_inside.html
```

4) Fixed-size (non-responsive) canvas
```bash
python cli.py \
  --T 0.05 \
  --backend plotly \
  --fixed_size \
  --width 1100 \
  --height 900 \
  --plotly zgrid_fixed.html
```

5) Tidy title + explicit sets
```bash
python cli.py \
  --T 0.05 \
  --backend plotly \
  --legend_mode minimal \
  --zetas 0.1 0.2 0.3 0.4 0.6 0.8 \
  --wnT 0.5 1 1.5 2 \
  --wd_over_ws 0 0.1 0.2 0.25 0.3 0.4 0.5 \
  --plotly zgrid_tidy.html
```

## C) Overlays from `in/` — CSV / JSON

Place your overlay files in `in/`. You said you have:
```
in/pz.csv
in/pz_alt.csv
in/overlay.json
in/pz.json
```
The CLI automatically resolves relative paths against `in/`. You can also pass absolute paths if you prefer.

### 1) Single JSON overlay (e.g., `in/overlay.json`)
```bash
python cli.py \
  --T 0.05 \
  --backend mpl \
  --pz overlay.json \
  --png zgrid_overlay_json.png
```

### 2) Single JSON overlay (alternate file, `in/pz.json`) + Plotly
```bash
python cli.py \
  --T 0.05 \
  --backend plotly \
  --pz pz.json \
  --plotly zgrid_overlay_pzjson.html
```

### 3) Single CSV overlay (e.g., `in/pz.csv`) with labels
```bash
python cli.py \
  --T 0.05 \
  --backend mpl \
  --pz pz.csv \
  --png zgrid_overlay_csv.png
```
**CSV header examples supported**
- `re,im,kind,label`
- `z,type,name`
- `re,im` (kind defaults to `pole`)

### 4) Alternate CSV overlay (e.g., `in/pz_alt.csv`) + Plotly
```bash
python cli.py \
  --T 0.05 \
  --backend plotly \
  --pz pz_alt.csv \
  --plotly zgrid_overlay_pzalt.html
```

### 5) Multiple overlays combined (CSV + JSON)
```bash
python cli.py \
  --T 0.05 \
  --backend mpl \
  --pz pz.csv overlay.json \
  --png zgrid_overlay_combo.png
```

### 6) Overlays + CSV export of curves
```bash
python cli.py \
  --T 0.05 \
  --backend mpl \
  --pz pz.csv pz.json \
  --export_csv_prefix zgrid_curves_with_overlay \
  --png zgrid_overlay_export.png
```

## D) Class diagram (PlantUML)
```bash
python tools/class_diagram.py
# => writes ./out/zGridTool_class_diagram.puml
```

## Notes
- For Plotly PNG snapshots, install `kaleido` for `fig.write_image` support.
- For large overlays, you can repeat `--pz` multiple times or list multiple files after one `--pz`.
- If a relative overlay path does not exist in `in/`, absolute paths are accepted.

### Sphinx

python -m system_design.zGridTool.cli sphinx-skel system_design/zGridTool/docs
python -m sphinx -b html docs docs/_build/html
open docs/_build/html/index.html
sphinx-autobuild docs docs/_build/html