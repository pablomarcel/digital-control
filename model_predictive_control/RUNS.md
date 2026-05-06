# model_predictive_control RUNS

Run these commands from the repository root or from inside the `model_predictive_control` package folder.

## Inspect package folders

```bash
python -m cli tree
```

## Check installed MPC-related libraries

```bash
python -m cli check-libs
```

## Create example input files

```bash
python -m cli init-examples
```

Overwrite examples if needed:

```bash
python -m cli init-examples \
  --force
```

## List example input files

```bash
python -m cli list-examples
```

## Native SciPy/SLSQP route: double integrator

```bash
python -m cli run in/double_integrator_mpc.json
```

## Native SciPy/SLSQP route: automotive engine cooling demo

```bash
python -m cli run in/automotive_engine_cooling_mpc.json
```

## CasADi Opti/IPOPT route: double integrator

```bash
python -m cli run in/double_integrator_mpc_casadi.json
```

## CasADi Opti/IPOPT route: automotive engine cooling demo

```bash
python -m cli run in/automotive_engine_cooling_mpc_casadi.json
```

## Send outputs to the package out folder with an explicit stem

```bash
python -m cli run in/double_integrator_mpc_casadi.json \
  --out out \
  --stem double_integrator_casadi
```

```bash
python -m cli run in/automotive_engine_cooling_mpc_casadi.json \
  --out out \
  --stem cooling_casadi
```

## Run without plots

```bash
python -m cli run in/double_integrator_mpc_casadi.json \
  --no-plots
```

## Send outputs to a custom folder

```bash
python -m cli run in/automotive_engine_cooling_mpc.json \
  --out out/mpc/out \
  --stem cooling_demo
```

## Self-test the native route

```bash
python -m cli self-test
```

## Self-test the CasADi route

```bash
python -m cli self-test-casadi
```

##

```bash
python sandbox/plot_discrete_time.py \
  out/discrete_time_system/double_integrator_step.csv
```