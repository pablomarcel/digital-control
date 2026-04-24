from __future__ import annotations
from typing import List, Iterable, Tuple, Dict, Any
import json, os
from .utils import ensure_dir_for
def parse_coeffs(s: str) -> List[float]:
    s = s.strip().replace(';', ','); return [float(x) for x in s.split(',') if x.strip()!='']
def parse_complex_list(s: str): return [complex(t.strip()) for t in s.replace(';',',').split(',') if t.strip()]
def save_json(path: str, payload: Dict[str, Any]):
    ensure_dir_for(path); open(path, 'w').write(json.dumps(payload, indent=2))
def save_csv(path: str, rows: Iterable[Tuple[str, list]]):
    ensure_dir_for(path)
    with open(path,'w') as f:
        f.write('name,coeff_descending\n')
        for name, coeffs in rows:
            f.write(f"{name},\"{','.join(str(float(c)) for c in coeffs)}\"\n")
