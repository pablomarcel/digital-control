# zTransformTool (digitalControl.zTransform)

Object-oriented refactor of the standalone `ztransform.py` into a testable, scalable package.

## Layout
```
zTransform/zTransformTool/
  app.py      # Orchestration
  apis.py     # RunRequest schema
  core.py     # Pure math/logic
  design.py   # Presentation helpers
  io.py       # Parsing + exports
  utils.py    # Symbols, paths, pretty boxes
  cli.py      # CLI entrypoint with import shim
  tools/
    class_diagram.py   # emits ./out/zTransformTool_class_diagram.puml
  tests/
    test_1.py
    test_2.py
  in/
  out/
```

## CLI
Run from repo root **or** inside the package:
```bash
python -m z_transform.zTransformTool.cli --help
# or
python z_transform/zTransformTool/cli.py --help
```

### Examples
```bash
# Forward Z
python -m z_transform.zTransformTool.cli --z --expr "sin(w*T*k)" --subs "T=1,w=0.5"

# Inverse Z (sequence to N)
python -m z_transform.zTransformTool.cli --iz --X "z**-1/(1 + z**-1)" --N 8 --export_json x.json

# Series (z^{-1})
python -m z_transform.zTransformTool.cli --series --X "z**-1/(1 + z**-1)" --N 6

# SciPy residuez
python -m z_transform.zTransformTool.cli --residuez --num "0 0.4673 -0.3393" --den "1 -1.5327 0.6607"

# python-control TF utilities
python -m z_transform.zTransformTool.cli --tf --num "0 0.4673 -0.3393" --den "1 -1.5327 0.6607" --impulse --N 40

# Difference equation
python -m z_transform.zTransformTool.cli --diff --a "1 3 2" --ics "x0=0,x1=1" --N 8
```

## Class Diagram
```bash
python z_transform/zTransformTool/tools/class_diagram.py
# => z_transform/zTransformTool/out/zTransformTool_class_diagram.puml
```
