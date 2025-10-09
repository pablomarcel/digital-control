
from __future__ import annotations
from typing import Optional, List, Dict, Any
import json, os
import numpy as np
from .utils import pkg_outdir

def fmt_mat(M: np.ndarray, width: int = 10, prec: int = 6) -> str:
    fmt = f"{{:>{width}.{prec}g}}"
    return "\n".join(" ".join(fmt.format(complex(v)) for v in r) for r in M)

def write_report(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

def capture_pretty_text(**kwargs) -> str:
    # Build a pretty report like the original script printed
    parts = []
    parts.append("\n=== Observability (Ogata) ===")
    parts.append(f"System type: {'discrete-time' if kwargs.get('discrete') else 'continuous-time'}")
    parts.append(f"n (states) = {kwargs.get('n')}, m (outputs) = {kwargs.get('m')}")
    parts.append(f"Eigenvalues(A): {kwargs.get('eigvals')}")
    parts.append("\nObsv = [C; CA; ...; CA^{n-1}]  (numeric rows)")
    parts.append(fmt_mat(kwargs.get('Obsv')))
    parts.append(f"\nrank(Obsv) = {kwargs.get('rank')}  ->  {'OBSERVABLE ✅' if kwargs.get('full') else 'NOT observable ❌'}")
    if kwargs.get('sym_rank') is not None:
        parts.append(f"rank(Obsv) [SymPy exact] = {kwargs.get('sym_rank')}")

    if kwargs.get('pbh_details') is not None:
        parts.append("\nPBH (dual) test: rank([λI - A*, C*]) must equal n for all eigenvalues λ.")
        for item in kwargs['pbh_details']:
            lam = item['lambda']
            parts.append(f"  λ={lam:>12}  rank={item['rank']:>2}  σ_min={item['sigma_min']:.3e}  "
                         f"{'OK' if item['pass'] else 'FAIL'}")

    if kwargs.get('gram_used') is not None:
        parts.append("\nInfinite-horizon Observability Gramian:")
        if kwargs.get('discrete'):
            parts.append(f"  stable? (ρ(A)<1) -> {kwargs.get('stability')}")
        else:
            parts.append(f"  stable? (Re(λ)<0) -> {kwargs.get('stability')}")
        parts.append(f"  Wo ({kwargs.get('gram_used')}) min eig ≈ {kwargs.get('gram_min_eig'):.3e}  "
                     f"-> {'PD ✅' if kwargs.get('gram_posdef') else 'not PD ❌'}")

    if kwargs.get('W_finite') is not None:
        parts.append(f"\nfinite-horizon Observability Gramian ({kwargs.get('finite_used')}, horizon={kwargs.get('finite_horizon')}):")
        parts.append(f"  min eig ≈ {kwargs.get('finite_min_eig'):.3e}")
    return "\n".join(parts)
