# intro/dacTool — RUNS.md

Run commands **from inside** `intro/dacTool` (import shim enabled). Inputs default to `in/`; outputs to `out/`.

```bash
python cli.py \
  --help
```

## R-2R ladder
```bash
# Minimal
python cli.py r2r \
  --csv codes.csv \
  --nbits 10 \
  --vref 3.3 \
  --R 10000 \
  --out r2r_results.csv \
  --trace r2r.vcd \
  --vcd-ideal
```

```bash
# With mismatch and analog path errors
python cli.py r2r \
  --csv codes.csv \
  --nbits 12 \
  --vref 3.3 \
  --R 10000 \
  --sigma-r-pct 0.1 \
  --sigma-2r-pct 0.1 \
  --gain-err 0.002 \
  --vo-offset 0.001 \
  --out r2r_nonideal.csv \
  --trace r2r_nonideal.vcd \
  --vcd-ideal
```

## Weighted-resistor
```bash
# Minimal
python cli.py weighted \
  --csv codes.csv \
  --nbits 10 \
  --vref 3.3 \
  --gain 1.0 \
  --out dac_results.csv \
  --trace dac.vcd
```

```bash
# With mismatch
python cli.py weighted \
  --csv codes.csv \
  --nbits 8 \
  --vref 3.3 \
  --gain 1.0 \
  --res-sigma-pct 0.2 \
  --gain-err 0.003 \
  --vo-offset 0.002 \
  --out dac_nonideal.csv \
  --trace dac_nonideal.vcd
```

## Tools
```bash
# PlantUML class diagram
python tools/class_diagram.py \
  --out out
# => out/dacTool_class_diagram.puml
```

### Sphinx

python -m introduction.dacTool.cli sphinx-skel introduction/dacTool/docs
python -m sphinx -b html docs docs/_build/html
open docs/_build/html/index.html
sphinx-autobuild docs docs/_build/html