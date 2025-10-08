
from __future__ import annotations
import json
from typing import List, Optional, Tuple, Dict, Any
import sympy as sp

from .utils import in_path, out_path

def parse_token(tok: str, var: sp.Symbol, K: Optional[sp.Symbol], rational: bool) -> sp.Expr:
    loc = {str(var): var}
    if K is not None:
        loc['K'] = K
    if rational:
        try:
            return sp.nsimplify(tok, rational=True, locals=loc)
        except Exception:
            pass
    return sp.sympify(tok, locals=loc)

def poly_from_coeffs(coeffs: List[str], var_name="z", param_name: Optional[str]=None, rational=False):
    """
    Returns: (z, K, P, a_fwd) where a_fwd are a0..an (high->const)
    """
    z = sp.symbols(var_name, complex=True)
    K = sp.symbols(param_name, real=True) if param_name else None
    a = [parse_token(c, z, K, rational) for c in coeffs]  # a0..an
    n = len(a) - 1
    P = sp.Integer(0)
    for k, ak in enumerate(a):
        P += ak * z**(n-k)
    return z, K, sp.expand(P), a

def load_from_json(json_name: str, rational: bool):
    data = json.loads(in_path(json_name).read_text())
    coeffs = data["coeffs"]
    var_name = data.get("variable", "z")
    param_name = data.get("param", None)
    return poly_from_coeffs(coeffs, var_name=var_name, param_name=param_name, rational=rational)

def dump_table(text: str, name: str) -> str:
    p = out_path(name)
    p.write_text(text)
    return str(p)

def dump_json(obj: Dict[str, Any], name: str) -> str:
    p = out_path(name)
    import json as _json
    p.write_text(_json.dumps(obj, indent=2))
    return str(p)
