
# README — `systemDesign.juryTestTool` (Ogata §4 — Jury/Schur–Cohn/Bilinear–Routh)

Run commands from **inside the package**:

```bash
cd digitalControl/systemDesign/juryTestTool
```

```bash
python cli.py --help
```

Outputs default to `./out/` in this package.

## 1) Example 4-4 (numeric, stable) — run each method + all

```bash
# Jury only
python cli.py --coeffs "1, -1.2, 0.07, 0.3, -0.08" \
  --method jury --save_table ex44_jury.txt --save_json ex44_jury.json
```

```bash
# Schur–Cohn only
python cli.py --coeffs "1, -1.2, 0.07, 0.3, -0.08" \
  --method schur --save_table ex44_schur.txt --save_json ex44_schur.json
```

```bash
# Bilinear–Routh only
python cli.py --coeffs "1, -1.2, 0.07, 0.3, -0.08" \
  --method bilinear --save_table ex44_routh.txt --save_json ex44_routh.json
```

```bash
# All methods together
python cli.py --coeffs "1, -1.2, 0.07, 0.3, -0.08" \
  --method all --save_table ex44_tables.txt --save_json ex44_all.json
```

## 2) Example 4-5 (third-order, P(1)=0 ➜ critical)

```bash
python cli.py --coeffs "1, -1.1, -0.1, 0.2" \
  --method all --save_table ex45_tables.txt --save_json ex45_all.json
```

## 3) Example 4-6 (third-order, unstable)

```bash
python cli.py --coeffs "1, -1.3, -0.08, 0.24" \
  --method all --save_table ex46_tables.txt --save_json ex46_all.json
```

## 4) Example 4-7 (second-order with gain K)

```bash
# 4a) Create JSON input
cat > in/ex47.json <<'JSON'
{
  "variable": "z",
  "param": "K",
  "coeffs": ["1", "(0.3679*K - 1.3679)", "(0.3679 + 0.2642*K)"]
}
JSON
```

```bash
# 4b) Solve K-range with each method
python cli.py --json_in ex47.json --method jury --solve_range \
  --save_table ex47_jury.txt --save_json ex47_jury.json
```

```bash
python cli.py --json_in ex47.json --method schur --solve_range \
  --save_table ex47_schur.txt --save_json ex47_schur.json
```

```bash
python cli.py --json_in ex47.json --method bilinear --solve_range \
  --save_table ex47_routh.txt --save_json ex47_routh.json
```

```bash
# 4c) All three at once
python cli.py --json_in ex47.json --method all --solve_range \
  --save_table ex47_tables.txt --save_json ex47_all.json
```

```bash
# 4d) Evaluate at specific K (inside range, and near upper bound)
python cli.py --json_in ex47.json --method all --eval_K 1.0
```

```bash
python cli.py --json_in ex47.json --method all --eval_K 2.3925 --T 1
```

## 5) Optional: exact-arithmetic (rational) runs

```bash
python cli.py --json_in ex47.json --method all --solve_range --rational \
  --save_table ex47_tables_rational.txt --save_json ex47_all_rational.json
```

## 6) Tools

```bash
# Generate PlantUML class diagram source
python tools/class_diagram.py
# -> out/juryTestTool_class_diagram.puml
```
