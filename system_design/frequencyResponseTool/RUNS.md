# RUNS — `systemDesign/frequencyResponseTool` (inside-package commands)

These commands are designed to be run **from inside** the package directory:

```bash
cd digitalControl/system_design/frequencyResponseTool
```

- Inputs live in `./in/` (convention only).
- Outputs are written to `./out/` unless you override with `--out=...`.
- All examples use **equals-style** flags to play nice with zsh.

---

## Quick help
```bash
python cli.py --help
```

## A) Inspect plant only (no compensator), Plotly SVG
```bash
python cli.py --T=0.2 --gz-num="0.01873, 0.01752" --gz-den="1, -1.8187, 0.8187" --comp=none --plot=plotly --plotly-output=svg --out=out
```

## B) Manual lead (Ogata 4‑12 style), both plotters
```bash
python cli.py --T=0.2 --gz-num="0.01873, 0.01752" --gz-den="1, -1.8187, 0.8187" --comp=lead --K=1.0 --alpha=0.361 --tau=0.979 --plot=matplotlib --save-mpl --plot=plotly --plotly-output=html --out=out
```

## C) Auto design from specs (lead), Plotly PNG
```bash
python cli.py --T=0.2 --gz-num="0.01873, 0.01752" --gz-den="1, -1.8187, 0.8187" --comp=auto --pm=50 --gm=10 --Kv=2 --plot=plotly --plotly-output=png --out=out
```

## D) Manual lag, Matplotlib PNGs
```bash
python cli.py --T=0.2 --gz-num="0.01873, 0.01752" --gz-den="1, -1.8187, 0.8187" --comp=lag --K=1.7 --beta=4.0 --tau=0.5 --plot=matplotlib --save-mpl --out=out
```

## E) Manual lag–lead, Plotly HTML
```bash
python cli.py --T=0.2 --gz-num="0.01873, 0.01752" --gz-den="1, -1.8187, 0.8187" --comp=laglead --K=1.0 --beta=4.0 --tau-lag=0.8 --alpha=0.4 --tau-lead=0.2 --plot=plotly --plotly-output=html --out=out
```

## F) Save unit-step response CSV (no plots required)
```bash
python cli.py --T=0.2 --gz-num="0.01873, 0.01752" --gz-den="1, -1.8187, 0.8187" --comp=lead --K=1.0 --alpha=0.361 --tau=0.979 --step=60 --out=out
```

## G) Matplotlib-only PNGs (no Plotly)
```bash
python cli.py --T=0.2 --gz-num="0.01873, 0.01752" --gz-den="1, -1.8187, 0.8187" --comp=none --plot=matplotlib --save-mpl --out=out
```

## H) Plotly PDF export
```bash
python cli.py --T=0.2 --gz-num="0.01873, 0.01752" --gz-den="1, -1.8187, 0.8187" --comp=none --plot=plotly --plotly-output=pdf --out=out
```

---

## Tools
### Generate PlantUML class diagram
```bash
python tools/class_diagram.py --out out
```
