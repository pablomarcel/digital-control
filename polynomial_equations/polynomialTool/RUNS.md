# polynomialTool — Run Commands (from inside the package)

> **Location:** run all commands from inside `polynomialEquations/polynomialTool/`  
> **Help:** `python cli.py --help` and `python cli.py <subcmd> --help`

Subcommands: `solve`, `polydesign`, `rst`, `modelmatch`

---

## 0) Quick sanity check
```bash
python cli.py --help
python cli.py solve --help
python cli.py polydesign --help
python cli.py rst --help
python cli.py modelmatch --help
```

Common flags (snake_case): `--layout {ogata,desc}`, `--d`, `--degS`, `--degR`, `--pretty`, `--show_E`,  
`--backend {mpl,plotly,none}`, `--save`, `--T`, `--kmax`, `--export_json`, `--export_csv`, `--ogata_parity` (where applicable).

> **Note:** This CLI uses underscore flags (e.g., `--show_E`, `--export_json`). Hyphenated forms like `--show-E` are not accepted.

---

## 1) Solve (Diophantine)

### 1.1 Ogata layout (Example 7-1 — show Sylvester E, pretty)
Expected: `alpha ≈ [1.0, -1.2]`, `beta ≈ [0.2, 0.3]` and a 4×4 Sylvester `E`.
```bash
python cli.py solve   --A "1,1,0.5"   --B "1,2"   --D "1,0,0,0"   --layout ogata   --pretty   --show_E
```

### 1.2 Descending layout (explicit square system)
```bash
python cli.py solve   --A "1,-1"   --B "1"   --D "1,0"   --layout desc   --degS 0 --degR 0   --show_E
```

### 1.3 Non‑square in DESC (falls back to least‑squares)
```bash
python cli.py solve   --A "1,0.5,0.25"   --B "1"   --D "1"   --layout desc
```

### 1.4 Export results (JSON/CSV)
```bash
python cli.py solve   --A "1,1,0.5"   --B "1,2"   --D "1,0,0,0"   --layout ogata   --export_json out/solve_7_1.json   --export_csv  out/solve_7_1.csv
```

---

## 2) polydesign (closed‑loop preview; step/ramp plots)

> `--config 2` enables the step/ramp preview path (mirrors the original examples).

### 2.1 Example 7‑2 (Plotly output)
```bash
python cli.py polydesign   --A "1,-2,1" --B "0.02,0.02"   --H "1,-1.2,0.52" --F "1,0"   --layout ogata --config 2   --backend plotly --kmax 40   --save out/ex7_2_plotly
```
Outputs: `out/ex7_2_plotly_step.html`, `out/ex7_2_plotly_ramp.html`.

### 2.2 MPL output + exports
```bash
python cli.py polydesign   --A "1,-2,1" --B "0.02,0.02"   --H "1,-1.2,0.52" --F "1,0"   --layout ogata --config 2   --backend mpl --kmax 60   --save out/pd_cfg2_mpl   --export_json out/pd_cfg2_mpl.json   --export_csv  out/pd_cfg2_mpl.csv
```

### 2.3 Fast, no-plot dry‑run (exports only)
```bash
python cli.py polydesign   --A "1,-2,1" --B "0.02,0.02"   --H "1,-1.2,0.52" --F "1,0"   --layout ogata --config 2   --backend none --kmax 1   --export_json out/pd_no_plot.json
```

---

## 3) rst (RST design)

> This subcommand **does not** take `--config`; parity can be requested with `--ogata_parity`.

### 3.1 Example 7‑3 (Plotly output, Ogata parity)
```bash
python cli.py rst   --A "1,-2,1" --B "0.02,0.02"   --H "1,-1.2,0.52" --F "1,0"   --layout ogata   --ogata_parity   --backend plotly --kmax 40   --save out/ex7_3/ex7_3_plotly
```
Outputs: `out/ex7_3/ex7_3_plotly_step.html`, `..._ramp.html`.

### 3.2 MPL output + export
```bash
python cli.py rst   --A "1,-2,1" --B "0.02,0.02"   --H "1,-1.2,0.52" --F "1,0"   --layout ogata   --ogata_parity   --backend mpl --kmax 40   --save out/rst_cfg2_mpl   --export_json out/rst_cfg2_mpl.json
```

### 3.3 Minimal, no‑plot check
```bash
python cli.py rst   --A "1,-2,1" --B "0.02,0.02"   --H "1,-1.2,0.52" --F "1,0"   --layout ogata   --backend none --kmax 1
```

---

## 4) modelmatch (Example 7‑4)

Required: `--Gmodel_num`, `--Gmodel_den`, `--H1`, `--F`.

### 4.1 Plotly output
```bash
python cli.py modelmatch   --A "1,-1.3679,0.3679" --B "0.3679,0.2642"   --Gmodel_num "0.62,-0.3" --Gmodel_den "1,-1.2,0.52"   --H1 "1,0.5" --F "1,0"   --layout ogata   --backend plotly --kmax 40   --save out/ex7_4/ex7_4_plotly
```

### 4.2 Fast, no‑plot, JSON export
```bash
python cli.py modelmatch   --A "1,-1.3679,0.3679" --B "0.3679,0.2642"   --Gmodel_num "0.62,-0.3" --Gmodel_den "1,-1.2,0.52"   --H1 "1,0.5" --F "1,0"   --layout ogata   --backend none --kmax 5   --export_json out/mm_fast.json
```

---

## 5) Tips

- **Pretty printing:** add `--pretty` where supported to show Sympy‑styled output.
- **Show Sylvester E:** add `--show_E` on `solve` to print the matrix (useful for checks).
- **Output dirs:** the CLI will create `out/` paths if they don’t exist.
- **Layouts:** `ogata` matches textbook ordering, `desc` uses descending powers; in `desc`, you may need `--degS/--degR` for square systems.
- **Backends:** `plotly` (HTML outputs), `mpl` (PNG/Matplotlib windows or saved figures), `none` (skip plotting but still compute/emit exports).