
# stateSpace.stateSolverTool — RUNS

Run these **from inside** `digitalControl/stateSpace/stateSolverTool/`:

```bash
python cli.py --help
```

## Examples

### Ogata 5-2 (console only, brief check)
```bash
python cli.py --example ogata_5_2
```

### Ogata 5-2 (LaTeX to console + brief check)
```bash
python cli.py --example ogata_5_2 --latex
```

### Ogata 5-2 (LaTeX, real modal blocks, integer power style, brief check to file)
```bash
python cli.py --example ogata_5_2 --latex --realblocks --power-style integer --latex-out ogata_5_2.tex
```

### Ogata 5-3 (console only)
```bash
python cli.py --example ogata_5_3
```

### Ogata 5-3 (LaTeX to file)
```bash
python cli.py --example ogata_5_3 --latex --latex-out ogata_5_3.tex
```

## Custom LTI

Same as 5-2 but via explicit matrices/vectors:
```bash
python cli.py \
  --mode lti \
  --G "[[0,1],[-0.16,-1]]" \
  --H "[[1],[1]]" \
  --C "[[1,0]]" \
  --D "[[0]]" \
  --x0 "[1,-1]" \
  --u "1" \
  --steps 6 \
  --check brief
```

With real modal blocks + LaTeX:
```bash
python cli.py \
  --mode lti \
  --G "[[0,1],[-0.16,-1]]" \
  --H "[[1],[1]]" \
  --C "[[1,0]]" \
  --D "[[0]]" \
  --x0 "[1,-1]" \
  --u "1" \
  --realblocks \
  --latex
```

With z-transform block + LaTeX to file:
```bash
python cli.py \
  --mode lti \
  --G "[[0,1],[-0.16,-1]]" \
  --H "[[1],[1]]" \
  --C "[[1,0]]" \
  --D "[[0]]" \
  --x0 "[1,-1]" \
  --u "1" \
  --latex --zt --latex-out lti_zt.tex
```

Diagonal system, geometric input \(u(k)=(0.9)^k\) to trigger \(U(z)\); LaTeX + zt:
```bash
python cli.py \
  --mode lti \
  --G "[[0.5,0],[0,0.3]]" \
  --H "[[1],[0]]" \
  --C "[[1,0]]" \
  --D "[[0]]" \
  --x0 "[0,0]" \
  --u "0.9**k" \
  --latex --zt
```

Same diagonal, integer power style formatting:
```bash
python cli.py \
  --mode lti \
  --G "[[0.5,0],[0,0.3]]" \
  --H "[[1],[0]]" \
  --C "[[1,0]]" \
  --D "[[0]]" \
  --x0 "[0,0]" \
  --u "0.9**k" \
  --power-style integer \
  --latex --zt --latex-out lti_geom_integer_style.tex
```

## LTV demo

Time-varying \(G(k)\); sequence + Phi(k,h) + LaTeX to file:
```bash
python cli.py \
  --mode ltv \
  --Gk "[[0,1],[-0.1 - 0.05*k, -1]]" \
  --Hk "[[1],[1]]" \
  --Ck "[[1,0]]" \
  --Dk "[[0]]" \
  --x0 "[1,-1]" \
  --u "1" \
  --steps 5
```

## Tools

Generate a PlantUML class diagram file:
```bash
python tools/class_diagram.py
# Produces: ./out/stateSolverTool_class_diagram.puml
```
