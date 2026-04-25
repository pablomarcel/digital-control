
# stateSpace.stateSpaceTool - RUNS.md

Run commands to execute from inside the package directory.

```bash
cd digitalControl/state_space/stateSpaceTool
python cli.py --help
```

## 1) Ogata Example 5-1
```bash
python cli.py --example ogata_5_1
```

## 2) z^{-1} coefficients (Ogata 5-6 layout)
```bash
python cli.py --form zmin1 --den "1 1.3 0.4" --num "0 1 1"
```

## 3) ZPK form
```bash
python cli.py --form zpk --zeros "-1" --poles "-0.5 -0.8" --gain 1
```

## 4) Complex pair -> real 2x2 (diagonal + Jordan views)
```bash
python cli.py --form expr --num "1" --den "z**2 - 0.2*z + 0.9" --forms "diag,jordan" --realblocks
```

## 5) JSON and LaTeX exports
```bash
mkdir -p out
```

```bash
python cli.py --example ogata_5_1 --json-out out/ogata_5_1_ss.json --latex-out out/ogata_5_1.tex --check brief
```

### Sphinx

python -m state_space.stateSpaceTool.cli sphinx-skel state_space/stateSpaceTool/docs
python -m sphinx -b html docs docs/_build/html
open docs/_build/html/index.html
sphinx-autobuild docs docs/_build/html