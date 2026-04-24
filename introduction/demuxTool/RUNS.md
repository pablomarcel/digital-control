# intro.demuxTool — N-way demultiplexer (PyRTL)

Run **from inside the package**:

```bash
cd digitalControl/introduction/demuxTool
```

```bash
python cli.py --help
```

## Examples

**CSV in `in/`, CSV + VCD out to `out/`:**
```bash
python cli.py --csv in/vectors_demux.csv --out results_demux.csv --trace demux.vcd
```

**Inline JSON vectors:**
```bash
python cli.py --json '[{"sel":0,"x":1},{"sel":1,"x":3},{"sel":2,"x":15}]' --n 4 --bits 8 --trace demux_inline.vcd
```

## Class diagram
(If Graphviz is not installed, this writes a DOT file at the given path.)
```bash
python tools/class_diagram.py --out out/demuxTool_class_diagram
```
