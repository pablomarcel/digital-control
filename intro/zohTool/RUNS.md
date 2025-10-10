# intro.zohTool — Zero-Order Hold (ZOH) simulator

Run commands from **inside the package directory**:

```bash
cd intro/zohTool
python cli.py --help
```

## 1) Minimal (CSV in, ideal ZOH, VCD + CSV out)

Create `in/u.csv`:

```
u
0
0.5
1.0
0.75
0.2
```

Run:
```bash
python cli.py --csv u.csv --Ts 1e-3 --units V --trace zoh.vcd --out zoh_results.csv
```

Outputs:
```
out/zoh.vcd
out/zoh_results.csv
```

## 2) JSON inline (quick test)
```bash
python cli.py --json '[0, 2, 2, 1, 3, 0.5]' --Ts 5e-4 --units V --trace zoh.vcd
```

## 3) Include transport delay (actuator latency)
```bash
python cli.py --csv u.csv --Ts 1e-3 --delay 2e-4 --trace zoh_delay.vcd
```

## 4) Model hold droop (capacitor leakage) with time constant τ
```bash
python cli.py --csv u.csv --Ts 1e-3 --droop-tau 0.02 --trace zoh_droop.vcd
```

## 5) Change value scaling (e.g., store millivolts instead of microvolts)
```bash
python cli.py --csv u.csv --Ts 1e-3 --scale 1e3 --units V --trace zoh_mV.vcd
```

## 6) CSV with explicit sample indices
Create `in/u_k.csv`:

```
k,u
0, 0.1
2, 0.5
3, 0.5
5, 0.0
```

Run:
```bash
python cli.py --csv u_k.csv --Ts 2e-3 --units V --trace zoh_sparse.vcd
```
