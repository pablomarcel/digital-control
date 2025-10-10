
# intro.muxTool — 4:1 multiplexer (PyRTL)

Run **from inside the package**:
```bash
cd digitalControl/intro/muxTool
python cli.py --help
```

## Examples
```bash
python cli.py --csv vectors.csv --out results.csv --trace mux.vcd
```
```bash
python cli.py --json '[{"sel":0,"d0":1,"d1":2,"d2":3,"d3":4},{"sel":1,"d0":5,"d1":6,"d2":7,"d3":8}]' --bits 8 --trace mux_inline.vcd
```

## Class diagram (Mermaid)
```bash
python tools/class_diagram.py --out out/muxTool_class_diagram
# Produces out/muxTool_class_diagram.mmd
```
