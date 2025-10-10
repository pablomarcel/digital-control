# intro.vcdTool — VCD waveform plotting

Run **from inside the package**:

```bash
cd digitalControl/intro/vcdTool
python cli.py --help
```

## Examples (auto-using `in/` and `out/`)

### MUX
```bash
python cli.py mux.vcd \
  --signals sel,d0,d1,d2,d3,y \
  --out-csv mux_traces.csv --png mux.png
```

### DEMUX
```bash
python cli.py demux.vcd \
  --signals sel,x,y0,y1,y2,y3 \
  --out-csv demux_traces.csv --backend plotly --html demux.html
```

### COUNTER (decode 10-bit bus)
```bash
python cli.py counter.vcd \
  --signals clk,cmp,code --decode code:10 \
  --backend plotly --html counter.html
```

### Counter–type ADC
```bash
python cli.py counter.vcd \
  --signals clk,cmp,code \
  --units us \
  --out-csv counter_traces.csv --png counter.png
```

### Generate class diagram (PlantUML)
```bash
python tools/class_diagram.py --out out
# => ./out/vcdTool_class_diagram.puml
```
