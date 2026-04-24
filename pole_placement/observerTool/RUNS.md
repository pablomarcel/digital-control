
# polePlacement.observerTool — RUNS

Run from inside the package:

```bash
cd digitalControl/pole_placement/observerTool
```

```bash
python cli.py --help
```

## Plotly step (HTML saved under ./out)

```bash
python cli.py sim \
  --A '1 0.2; 0 1' --B '0.02; 0.2' --C '1 0' \
  --K '8 3.2' --L '2; 5' \
  --Ts 0.2 --N 41 --ref step --K0 auto \
  --plotly --html step_plotly.html
```

## Min-order Ke

```bash
python cli.py design --type min \
  --A '1 0.2; 0 1' --B '0.02; 0.2' --C '1 0' \
  --poles '0' --method acker --csv ke.csv --out ke.json
```

## Separation principle check

```bash
python cli.py closedloop \
  --A '1 0.2; 0 1' --B '0.02; 0.2' --C '1 0' \
  --K '8 3.2' --L '2; 5' \
  --out sep.json
```

## K0 in Ogata mode

```bash
python cli.py k0 \
  --A '1 0.2; 0 1' --B '0.02; 0.2' --C '1 0' \
  --K '8 3.2' --L '2; 5' \
  --mode ogata --ogata-extra-gain 1.32 \
  --out k0_ogata.json
```
