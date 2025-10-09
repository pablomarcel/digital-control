# RUNS — polePlacement.servoTool (run INSIDE this package)

```bash
cd digitalControl/polePlacement/servoTool
```

## Help
```bash
python cli.py --help
```

## 1) Design (Ogata) with equations (stderr)
```bash
python cli.py design --G "0 1 0; 0 0 1; -0.12 -0.01 1" --H "0; 0; 1" --C "0.5 1 0" --which ogata --eq
```

## 2) Observer + equations to a file
```bash
python cli.py observer --config in/servo_6_13.yaml --eq --eq-file out/observer_eq.txt
```

## 3) Example end-to-end and equations
```bash
python cli.py example --eq
```

## 4) Sim (with observer) and print all one-liners to stdout
```bash
python cli.py sim --config in/servo_6_13.yaml --use-observer --eq --eq-stdout
```

### Extras
Matplotlib dots + equations:
```bash
python cli.py sim --config in/servo_6_13.yaml --use-observer --eq --eq-stdout --plot --savefig out/servo_step.png
```

Plotly interactive HTML + equations:
```bash
python cli.py sim --config in/servo_6_13.yaml --use-observer --eq --eq-stdout --plotly --html out/servo_interactive.html --open
```

Design (Ogata K-hat) with equations:
```bash
python cli.py design --config in/servo_6_13.yaml --which ogata --eq --eq-stdout
```

Min-order observer with equations:
```bash
python cli.py observer --config in/servo_6_13.yaml --eq --eq-stdout
```
