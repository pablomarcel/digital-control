# stateSpace.liapunovTool — RUNS

Run **from inside this package directory**:

```bash
cd state_space/liapunovTool
```

## Help

```bash
python cli.py --help
```

## Ogata examples
# Example 5-8 (CT)

```bash
python cli.py example ogata_5_8
```

```bash
python cli.py example ogata_5_8 --latex --latex-out out/ogata_5_8.tex
```

# Example 5-9 (DT)

```bash
python cli.py example ogata_5_9
```

```bash
python cli.py example ogata_5_9 --latex --latex-out out/ogata_5_9.tex
```

## Custom continuous-time (real)
```bash
python cli.py ct --A "[[0 1]; [-25 -4]]" --Q "[[1 0]; [0 1]]" --evalf 16
```

## Custom discrete-time (real)
```bash
python cli.py dt --G "[[0.970883 0.044847]; [-1.121176 0.791495]]" --Q "[[1 0]; [0 1]]" --evalf 16
```

## Complex/Hermitian
```bash
python cli.py ct --A "[[0, 1+i]; [-(1-i), -2]]" --Q "[[1 0]; [0 1]]" --hermitian --evalf 16
```

```bash
python cli.py dt --G "[[0, 1+i]; [-(1-i), -2]]" --Q "[[1 0]; [0 1]]" --hermitian --evalf 16
```

## Class diagram
```bash
python tools/class_diagram.py
# → writes ./out/liapunovTool_class_diagram.puml
```

### Sphinx

python -m quadratic_control.quadraticTool.cli sphinx-skel quadratic_control/quadraticTool/docs
python -m sphinx -b html docs docs/_build/html
open docs/_build/html/index.html
sphinx-autobuild docs docs/_build/html