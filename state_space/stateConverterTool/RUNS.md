
# stateSpace.stateConverterTool — ZOH Discretization + Pulse Transfer (Ogata §5‑4/§5‑5)

Object‑oriented refactor of the standalone `state_converter.py` into a testable package.

> **All commands below are intended to be run from _inside_ this package:**
>
> ```bash
> cd state_space/stateConverterTool
> ```

## Layout
```
stateSpace/stateConverterTool/
  app.py          # Orchestration & high-level run() pipeline
  apis.py         # Dataclasses for requests/responses (public API surface)
  cli.py          # CLI entry with import shim (run from inside the package)
  core.py         # Pure math engine (G(T), H(T), F(z))
  design.py       # Pretty printers, LaTeX builder
  io.py           # Parsing helpers, safe loads, path utils
  utils.py        # Decorators, small helpers
  tools/
    class_diagram.py  # Emits PlantUML .puml
  tests/
    test_core_numeric.py
    test_cli_examples.py
  in/             # sample inputs (reserved)
  out/            # outputs land here
```

---

## Quick help
```bash
python cli.py --help
```

---

## Built‑in examples (numeric fast path)

### MATLAB p.318 (Ogata) — default T=0.05
```bash
python cli.py --example matlab_p318 --evalf 16
```

### MATLAB p.318 with T = 0.2
```bash
python cli.py --example matlab_p318 --T 0.2 --evalf 16
```

### MATLAB p.318 with T = 1.0
```bash
python cli.py --example matlab_p318 --T 1 --evalf 16
```

### MATLAB p.318 + force explicit \((zI-G)^{-1}\)
```bash
python cli.py --example matlab_p318 --evalf 16 --force-inverse
```

### MATLAB p.318 + LaTeX to file
```bash
python cli.py --example matlab_p318 --evalf 16 --latex --latex-out out/matlab_p318.tex
```

---

## Symbolic textbook examples

### Ogata §5‑4 (symbolic \(a>0\), default \(T = T\))
```bash
python cli.py --example ogata_5_4
```

### Ogata §5‑4 with numeric sampling \(T = 0.1\)
```bash
python cli.py --example ogata_5_4 --T 0.1
```

### Ogata §5‑5 (default \(T = 1\))
```bash
python cli.py --example ogata_5_5
```

### Ogata §5‑5 + LaTeX out
```bash
python cli.py --example ogata_5_5 --latex --latex-out out/ogata_5_5.tex
```

---

## Explicit matrices (generic c2d + pulse TF)

### Fast numeric path (evalf=16)
```bash
python cli.py --A "[[0,1],[-25,-4]]" --B "[[0],[1]]" --C "[[1,0]]" --D "[[0]]" --T 0.05 --evalf 16
```

### Same, without simplify (speed test)
```bash
python cli.py --A "[[0,1],[-25,-4]]" --B "[[0],[1]]" --C "[[1,0]]" --D "[[0]]" --T 0.05 --evalf 16 --no-simplify
```

### Same, with explicit inverse printed
```bash
python cli.py --A "[[0,1],[-25,-4]]" --B "[[0],[1]]" --C "[[1,0]]" --D "[[0]]" --T 0.05 --evalf 16 --force-inverse
```

### Same, LaTeX to file
```bash
python cli.py --A "[[0,1],[-25,-4]]" --B "[[0],[1]]" --C "[[1,0]]" --D "[[0]]" --T 0.05 --evalf 16 --latex --latex-out out/c2d_example.tex
```

---

## Singular \(A\) handling (augmented expm fallback)

### Singular \(A\) with fallback enabled (default)
```bash
python cli.py --A "[[0,1],[0,0]]" --B "[[0],[1]]" --C "[[1,0]]" --D "[[0]]" --T 1
```

### Singular \(A\) with fallback disabled (expect failure)
```bash
python cli.py --A "[[0,1],[0,0]]" --B "[[0],[1]]" --C "[[1,0]]" --D "[[0]]" --T 1 --no-fallback
```

---

## Output & documentation helpers

### Emit LaTeX for any run (stdout only)
```bash
python cli.py --example matlab_p318 --evalf 16 --latex
```

### PlantUML class diagram
```bash
python tools/class_diagram.py
```

---

## Testing (package‑local)

### Quick
```bash
pytest state_space/stateConverterTool/tests -q
```

### With coverage report
```bash
pytest state_space/stateConverterTool/tests --override-ini addopts= --cov --cov-config=state_space/stateConverterTool/.coveragerc --cov-report=term-missing
```

---

## Tips
- Prefer `--evalf` when all inputs are numeric for dramatic speedups (no heavy symbolic simplification).
- Use `--no-simplify` during design sweeps; re‑enable for final nice forms.
- For SISO, `F(z)` prints as a scalar; for MIMO, you’ll get a matrix of rational entries.

### Sphinx

python -m quadratic_control.quadraticTool.cli sphinx-skel quadratic_control/quadraticTool/docs
python -m sphinx -b html docs docs/_build/html
open docs/_build/html/index.html
sphinx-autobuild docs docs/_build/html