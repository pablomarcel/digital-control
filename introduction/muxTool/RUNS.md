
# intro.muxTool — 4:1 multiplexer (PyRTL)

Run **from inside the package**:
```bash
cd digitalControl/introduction/muxTool
python cli.py \
  --help
```

## Examples
```bash
python cli.py \
  --csv vectors.csv \
  --out results.csv \
  --trace mux.vcd
```

```bash
python cli.py \
  --json '[{"sel":0,"d0":1,"d1":2,"d2":3,"d3":4},{"sel":1,"d0":5,"d1":6,"d2":7,"d3":8}]' \
  --bits 8 \
  --trace mux_inline.vcd
```

## Class diagram (Mermaid)
```bash
python tools/class_diagram.py \
  --out out/muxTool_class_diagram
# Produces out/muxTool_class_diagram.mmd
```

### Sphinx

python -m transient_analysis.hurwitzTool.cli sphinx-skel transient_analysis/hurwitzTool/docs
python -m sphinx -b html docs docs/_build/html
open docs/_build/html/index.html
sphinx-autobuild docs docs/_build/html