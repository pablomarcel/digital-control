# RUNS — `zTransform.zTransformTool` (Ogata Ch. 2, Ex. 2‑1 … 2‑19)

> **All commands are executed from inside this package directory**:
>
> ```bash
> cd z_transform/zTransformTool
> ```
>
> Use the local entrypoint:
>
> ```bash
> python cli.py --help
> ```

---

## Conventions

- **Inputs** (if any) live here: `./in/`  
- **Outputs** are written to `./out/` by default when you pass relative paths to `--export_csv/--export_json`.  
- Numbers in lists can be **space or comma separated**. Protect `*` with quotes in zsh.

---

## Quick help & sanity checks

```bash
python cli.py --help
```

```bash
python cli.py --z --expr "1" --N 3
```

---

## A) Forward Z‑transform (`--z`) and from sampled `x(t)` (`--zt`)

### A1) Ex 2‑1: \( \mathcal{Z}\{\cos(\omega kT)\} \)
```bash
python cli.py --z --expr "cos(w*T*k)" --subs "T=1,w=0.5" --pretty
```

### A2) Ex 2‑1 (sine companion): \( \mathcal{Z}\{\sin(\omega kT)\} \)
```bash
python cli.py --z --expr "sin(w*T*k)" --subs "T=1,w=0.5" --pretty
```

### A3) Ex 2‑2: From Laplace to Z via sampling \(x(t)=1-e^{-t}\), sample at \(t=kT\)
```bash
python cli.py --zt --xt "1 - exp(-t)" --subs "T=1" --pretty
```

### A4) Ex 2‑7: Complex translation (e^{-aTk} times trig)
```bash
python cli.py --z --expr "exp(-a*T*k)*sin(w*T*k)" --subs "T=1,a=0.3,w=1.2" --pretty
```

---

## B) Inverse Z‑transform (unilateral, robust) — `--iz`

### B1) Initial/Final value checks (Ex 2‑8/2‑9 variant)
```bash
python cli.py --iz --X "(1 - exp(-T))*z**-1/((1 - z**-1)*(1 - exp(-T)*z**-1))" --subs "T=1" --N 0
```

### B2) Alternating sequence (Ex 2‑11): \( X(z)=\frac{z^{-1}}{1+z^{-1}} \Rightarrow x[k]=(-1)^k \) for k≥1
```bash
python cli.py --iz --X "z**-1/(1 + z**-1)" --N 8 --pretty
```

### B3) Finite‑length sequence (Ex 2‑12): \( X(z)=1 + 2z^{-1} + 3z^{-2} + 4z^{-3} \)
```bash
python cli.py --iz --X "1 + 2*z**-1 + 3*z**-2 + 4*z**-3" --N 6 --export_json x_e212.json --pretty
```

### B4) Shifting theorem (Ex 2‑13): \( X(z)=\frac{z^{-1}}{1 - a z^{-1}} \)
```bash
python cli.py --iz --X "z**-1/(1 - a*z**-1)" --subs "a=0.7" --N 6 --pretty
```

### B5) PFE, two real poles (Ex 2‑14/2‑16 plant)
```bash
python cli.py --iz --X "(1 - exp(-a*T))*z/((z-1)*(z-exp(-a*T)))" --subs "a=1,T=1" --N 8 --pretty
```

### B6) Mixed real/complex poles (Ex 2‑15): \( \frac{z^2 + z + 2}{(z-1)(z^2 - z + 1)} \)
```bash
python cli.py --iz --X "(z**2 + z + 2)/((z-1)*(z**2 - z + 1))" --N 8 --pretty
```

### B7) Double pole variant (Ex 2‑17): \( \frac{z^2}{(z-1)^2 (z-e^{-aT})} \)
```bash
python cli.py --iz --X "z**2/((z-1)**2*(z-exp(-a*T)))" --subs "a=1,T=1" --N 6 --pretty
```

### B8) Diagnostic: list poles & residues for \(X(z) z^{k-1}\)
```bash
python cli.py --iz \
  --X "z*(1 - exp(-a*T))/((z-1)*(z-exp(-a*T)))" \
  --subs "a=1,T=1" \
  --N 6 --pretty
```

---

## C) Direct‑division series in \(z^{-1}\) — `--series`

### C1) Ex 2‑10: first 7 terms of \( X(z)=\frac{10z+5}{(z-1)(z-0.2)} \)
```bash
python cli.py --series --X "(10*z + 5)/((z-1)*(z-0.2))" --N 6 --export_csv series_e210.csv --pretty
```

### C2) Alternating sequence again
```bash
python cli.py --series --X "z**-1/(1 + z**-1)" --N 8
```

### C3) Geometric ratio 0.5 in \(z^{-1}\)
```bash
python cli.py --series --X "z**-1/(1 - 0.5*z**-1)" --N 8
```

---

## D) Computational path — SciPy & python‑control

### D1) SciPy `residuez` (partial fractions in \(z^{-1}\))
```bash
python cli.py --residuez --num "0 0.4673 -0.3393" --den "1 -1.5327 0.6607"
```

### D2) Discrete TF utilities (python‑control) — impulse
```bash
python cli.py --tf --num "0 0.4673 -0.3393" --den "1 -1.5327 0.6607" --impulse --N 40 --dt 1 --export_json tf_impulse.json
```

### D3) Discrete TF utilities — step
```bash
python cli.py --tf --num "0 0.4673 -0.3393" --den "1 -1.5327 0.6607" --step --N 40 --dt 1 --export_csv tf_step.csv
```

### D4) Discrete TF utilities — forced response to a finite input
```bash
python cli.py --tf --num "0 0.4673 -0.3393" --den "1 -1.5327 0.6607" --u "1 0 0 0 0 0 0 0 0 0" --N 40 --dt 1 --export_json tf_forced.json
```

---

## E) Difference equations — `--diff`

### E1) Ogata Ex 2‑18: \(x(k+2)+3x(k+1)+2x(k)=0,\; x(0)=0,\; x(1)=1\)
```bash
python cli.py --diff --a "1 3 2" --ics "x0=0,x1=1" --N 8 --pretty
```

### E2) Ogata Ex 2‑19 (symbolic): \(x(k+2)+(a+b)x(k+1)+ab\,x(k)=0\) with \(x(0),x(1)\)
```bash
python cli.py --diff --a "1 (a+b) a*b" --ics "x0=x0,x1=x1" --pretty
```

### E3) Non‑homogeneous: \(x(k+1)-x(k)=1,\; x(0)=0\Rightarrow x[k]=k\)
```bash
python cli.py --diff --a "1 -1" --rhs "1" --ics "x0=0" --N 6 --pretty
```

---

## F) Class diagram

```bash
python tools/class_diagram.py
```

> Produces: `./out/zTransformTool_class_diagram.puml`
