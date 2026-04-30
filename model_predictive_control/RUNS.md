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
python -m cli init-examples --force
```

## Run the constrained double-integrator MPC demo

```bash
python -m cli run model_predictive_control/in/double_integrator_mpc.json
```

Equivalent short form when running from inside the package folder:

```bash
python cli.py run in/double_integrator_mpc.json
```

## Run the automotive engine-cooling LTV MPC demo

```bash
python -m cli run model_predictive_control/in/automotive_engine_cooling_mpc.json
```

Equivalent short form when running from inside the package folder:

```bash
python cli.py run in/automotive_engine_cooling_mpc.json
```

## Send outputs to a custom folder

```bash
python -m cli run model_predictive_control/in/automotive_engine_cooling_mpc.json \
  --out model_predictive_control/out \
  --stem cooling_demo
```

## Run a quick package self-test

```bash
python -m cli self-test
```
