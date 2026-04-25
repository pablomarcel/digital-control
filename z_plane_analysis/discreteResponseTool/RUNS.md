# discreteResponseTool — RUNS.md (from inside the package)

Run every command **from this directory**:

```bash
cd z_plane_analysis/discreteResponseTool
```

The import shim in `cli.py` lets you run the tool as a script with absolute-package imports.  
Outputs land in `out/` if you either (a) pass `--outdir out` or (b) give filenames with no directory (the app prefixes them with `out/`). For deterministic paths below we include `--outdir out`.

> **Usage pattern:**  
> `python cli.py <args...> --outdir out`

## Contents
- [0.8 · scipy · base](#08--scipy--base)
  - [1. Ogata Example 3-7 (step, plots, panel, Plotly)](#1-ogata-example-3-7-step-plots-panel-plotly)
  - [2. Same system, log-spaced root-locus](#2-same-system-log-spaced-root-locus)
  - [3. Custom plant + analog PID mapping (auto positional), step](#3-custom-plant--analog-pid-mapping-auto-positional-step)
  - [4. Direct digital controller entry, step](#4-direct-digital-controller-entry-step)
  - [5. Pole-placement (no controller specified), desired CL poles](#5-pole-placement-no-controller-specified-desired-cl-poles)
  - [6. Ramp response (unit slope) on Example 3-7](#6-ramp-response-unit-slope-on-example-3-7)
- [0.9 · scipy · example 3-7 variants](#09--scipy--example-3-7-variants)
- [1.0 · scipy · prefilter](#10--scipy--prefilter)
- [1.3 · scipy · 2-DOF](#13--scipy--2-dof)
- [1.7 · root locus sweeps](#17--root-locus-sweeps)
- [1.9 · example 4-9 · controller trick](#19--example-4-9--controller-trick)
- [Tips](#tips)

## 0.8 · scipy · base

### 1. Ogata Example 3-7 (step, plots, panel, Plotly)

```bash
python cli.py \
  --example37 \
  --print-tf \
  --N 60 \
  --matplotlib ex_step.png \
  --csv ex_step.csv \
  --pzmap ex_pz.png \
  --pzclip 1.6 \
  --rlocus ex_rl.png \
  --kmin 0 \
  --kmax 20 \
  --rclip 1.6 \
  --plotly-step ex_step.html \
  --plotly-pz ex_pz.html \
  --plotly-rl ex_rl.html \
  --panel ex_panel.png \
  --outdir out
```

### 2. Same system, log-spaced root-locus

```bash
python cli.py \
  --example37 \
  --rlocus ex_rl_log.png \
  --rlocus-log \
  --kmin 1e-3 \
  --kmax 1e2 \
  --rclip 1.8 \
  --outdir out
```

### 3. Custom plant + analog PID mapping (auto positional), step

```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 1 0 \
  --T 0.5 \
  --K 2.0 \
  --Ti 1.0 \
  --Td 0.1 \
  --N 60 \
  --print-tf \
  --matplotlib analog_step.png \
  --pzmap analog_pz.png \
  --rlocus analog_rl.png \
  --kmax 40 \
  --rclip 2.0 \
  --outdir out
```

### 4. Direct digital controller entry, step

```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 1 0 \
  --T 0.1 \
  --ctrl-numz 0.1 0.09 \
  --ctrl-denz 1 -0.8 \
  --N 120 \
  --print-tf \
  --matplotlib direct_step.png \
  --pzmap direct_pz.png \
  --pzclip 1.6 \
  --rlocus direct_rl.png \
  --kmax 15 \
  --rclip 1.6 \
  --outdir out
```

### 5. Pole-placement (no controller specified), desired CL poles

```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 1 0 \
  --T 1 \
  --cl-poles 0.8 0.7+0.25j 0.7-0.25j 0.6 \
  --print-tf \
  --matplotlib place_step.png \
  --pzmap place_pz.png \
  --rlocus place_rl.png \
  --outdir out
```

### 6. Ramp response (unit slope) on Example 3-7

```bash
python cli.py \
  --example37 \
  --input ramp \
  --amp 1.0 \
  --N 40 \
  --matplotlib ramp.png \
  --csv ramp.csv \
  --plotly-step ramp.html \
  --outdir out
```

## 0.9 · scipy · example 3-7 variants

**A. Digital PID directly (no shortcut flag)**

```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 1 0 \
  --T 1 \
  --Kp 1 \
  --Ki 0.2 \
  --Kd 0.2 \
  --N 60 \
  --matplotlib ex_step.png \
  --pzmap ex_pz.png \
  --rlocus ex_rl.png \
  --outdir out
```

**B. Analog PID that maps to the above at T=1**

```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 1 0 \
  --T 1 \
  --K 1.1 \
  --Ti 5.5 \
  --Td 0.18181818 \
  --N 60 \
  --matplotlib ex_step.png \
  --pzmap ex_pz.png \
  --rlocus ex_rl.png \
  --outdir out
```

## 1.0 · scipy · prefilter

**1) Base pole-placement**

```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 1 0 \
  --T 1 \
  --cl-poles 0.8 "0.7+0.25j" "0.7-0.25j" 0.6 \
  --print-tf \
  --matplotlib place_step.png \
  --pzmap place_pz.png \
  --rlocus place_rl.png \
  --outdir out
```

**2) Wide K sweep (log scale)**

```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 1 0 \
  --T 1 \
  --cl-poles 0.8 "0.7+0.25j" "0.7-0.25j" 0.6 \
  --rlocus place_rl_log.png \
  --rlocus-log \
  --kmin 1e-3 \
  --kmax 1e2 \
  --rclip 2.0 \
  --outdir out
```

**3) Add prefilter  F(z)=(1-β)/(1-β z^{-1}), β=0.85**

```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 1 0 \
  --T 1 \
  --cl-poles 0.8 "0.7+0.25j" "0.7-0.25j" 0.6 \
  --pre-numz 0.15 \
  --pre-denz 1 -0.85 \
  --matplotlib place_step_pref.png \
  --pzmap place_pz_pref.png \
  --outdir out
```

**4) Alternate pole set**

```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 1 0 \
  --T 1 \
  --cl-poles 0.7 "0.65+0.2j" "0.65-0.2j" 0.55 \
  --matplotlib place_step_alt.png \
  --pzmap place_pz_alt.png \
  --rlocus place_rl_alt.png \
  --outdir out
```

**5) Same poles, different sampling time (T=0.5)**

```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 1 0 \
  --T 0.5 \
  --cl-poles 0.8 "0.7+0.25j" "0.7-0.25j" 0.6 \
  --matplotlib place_T05.png \
  --pzmap place_T05_pz.png \
  --rlocus place_T05_rl.png \
  --outdir out
```

## 1.3 · scipy · 2-DOF

**A. 2-DOF with DC tracking**

```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 1 0 \
  --T 1 \
  --cl-poles 0.8 "0.7+0.25j" "0.7-0.25j" 0.6 \
  --two-dof \
  --t-design dc \
  --print-tf \
  --matplotlib 2dof_dc_step.png \
  --pzmap 2dof_dc_pz.png \
  --rlocus 2dof_dc_rl.png \
  --outdir out
```

**B. 2-DOF with lag on reference (β=0.85)**

```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 1 0 \
  --T 1 \
  --cl-poles 0.8 "0.7+0.25j" "0.7-0.25j" 0.6 \
  --two-dof \
  --t-design lag \
  --t-beta 0.85 \
  --matplotlib 2dof_lag085_step.png \
  --pzmap 2dof_lag085_pz.png \
  --rlocus 2dof_lag085_rl.png \
  --outdir out
```

**C. 2-DOF “none” (baseline)**

```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 1 0 \
  --T 1 \
  --cl-poles 0.8 "0.7+0.25j" "0.7-0.25j" 0.6 \
  --two-dof \
  --t-design none \
  --matplotlib 2dof_none_step.png \
  --pzmap 2dof_none_pz.png \
  --rlocus 2dof_none_rl.png \
  --outdir out
```

**D. 2-DOF, faster pole set, DC design**

```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 1 0 \
  --T 1 \
  --cl-poles 0.7 "0.65+0.2j" "0.65-0.2j" 0.55 \
  --two-dof \
  --t-design dc \
  --matplotlib 2dof_alt_step.png \
  --pzmap 2dof_alt_pz.png \
  --rlocus 2dof_alt_rl.png \
  --outdir out
```

**E. 2-DOF, different sampling time (T=0.5)**

```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 1 0 \
  --T 0.5 \
  --cl-poles 0.8 "0.7+0.25j" "0.7-0.25j" 0.6 \
  --two-dof \
  --t-design dc \
  --matplotlib 2dof_T05_step.png \
  --pzmap 2dof_T05_pz.png \
  --rlocus 2dof_T05_rl.png \
  --outdir out
```

## 1.7 · root locus sweeps

**Matplotlib — three T values**

# T = 0.5 s
```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 1 \
  --T 0.5 \
  --Kp 0 \
  --Ki 1 \
  --Kd 0 \
  --rlocus ogata45_T05_rl.png \
  --rlocus-log \
  --kmin 1e-4 \
  --kmax 2e1 \
  --rclip 1.3 \
  --outdir out
```

# T = 1.0 s
```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 1 \
  --T 1 \
  --Kp 0 \
  --Ki 1 \
  --Kd 0 \
  --rlocus ogata45_T10_rl.png \
  --rlocus-log \
  --kmin 1e-4 \
  --kmax 1e1 \
  --rclip 1.3 \
  --outdir out
```

# T = 2.0 s
```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 1 \
  --T 2 \
  --Kp 0 \
  --Ki 1 \
  --Kd 0 \
  --rlocus ogata45_T20_rl.png \
  --rlocus-log \
  --kmin 1e-4 \
  --kmax 6 \
  --rclip 1.3 \
  --outdir out
```

**Same RL with direct controller entry**

```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 1 \
  --T 0.5 \
  --ctrl-numz 1 \
  --ctrl-denz 1 -1 \
  --rlocus ogata45_T05_rl_direct.png \
  --rlocus-log \
  --kmin 1e-4 \
  --kmax 2e1 \
  --rclip 1.3 \
  --outdir out
```

**Root locus (Plotly, interactive HTML)**

```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 1 \
  --T 0.5 \
  --Kp 0 \
  --Ki 1 \
  --Kd 0 \
  --plotly-rl ogata45_T05_rl.html \
  --rlocus-log \
  --kmin 1e-4 \
  --kmax 2e1 \
  --rclip 1.3 \
  --outdir out
```

**Closed-loop at K=2 (Ogata marks these poles)**

# T = 0.5 s
```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 1 \
  --T 0.5 \
  --Kp 0 \
  --Ki 2 \
  --Kd 0 \
  --N 40 \
  --print-tf \
  --matplotlib ogata45_T05_K2_step.png \
  --pzmap ogata45_T05_K2_pz.png \
  --pzclip 1.2 \
  --outdir out
```

# T = 1.0 s
```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 1 \
  --T 1 \
  --Kp 0 \
  --Ki 2 \
  --Kd 0 \
  --N 40 \
  --print-tf \
  --matplotlib ogata45_T10_K2_step.png \
  --pzmap ogata45_T10_K2_pz.png \
  --pzclip 1.2 \
  --outdir out
```

# T = 2.0 s
```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 1 \
  --T 2 \
  --Kp 0 \
  --Ki 2 \
  --Kd 0 \
  --N 40 \
  --print-tf \
  --matplotlib ogata45_T20_K2_step.png \
  --pzmap ogata45_T20_K2_pz.png \
  --pzclip 1.2 \
  --outdir out
```

## 1.9 · example 4-9 · controller trick

```bash
python cli.py \
  --plant-num 1 \
  --plant-den 1 2 0 \
  --T 0.2 \
  --ctrl-numz 1 \
  --ctrl-denz 1 \
  --print-tf \
  --rlocus e49_plant_rl.png \
  --rlocus-log \
  --kmin 1e-3 \
  --kmax 2e1 \
  --rclip 1.2 \
  --outdir out
```

## Tips

- To clear previous artifacts:
  ```bash
  rm -rf out/*
  ```
- Filenames without a directory part are placed under `--outdir` automatically.
- You can pass nested subpaths (e.g. `--matplotlib rl/ogata_T05.png`)—they’ll be created under `out/`.

### Sphinx

python -m z_plane_analysis.discreteResponseTool.cli sphinx-skel z_plane_analysis/discreteResponseTool/docs
python -m sphinx -b html docs docs/_build/html
open docs/_build/html/index.html
sphinx-autobuild docs docs/_build/html