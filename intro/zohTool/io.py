from __future__ import annotations
import csv, json, os
from typing import List, Dict, Any
from .utils import looks_inline_json

def load_u_from_csv(path: str) -> List[float]:
    """
    CSV formats accepted:
      1) 'u' column (values in order, k = row index)
      2) 'k','u' columns (k can be nonconsecutive; rows are sorted by k)
    """
    with open(path, newline='') as f:
        rdr = csv.DictReader(f)
        fields = [c.strip() for c in (rdr.fieldnames or [])]
        if 'u' not in fields:
            raise ValueError("CSV must contain a column named 'u' (and optional 'k').")
        rows = []
        for row in rdr:
            k = int(row['k']) if 'k' in row and row['k'] != '' else None
            u = float(row['u'])
            rows.append((k, u))
        # If k provided, sort and fill gaps with zeros (dense sequence)
        if any(k is not None for k, _ in rows):
            rows = sorted((k if k is not None else i, u) for i, (k, u) in enumerate(rows))
            kmin, kmax = rows[0][0], rows[-1][0]
            u_map = {k: u for k, u in rows}
            return [u_map.get(k, 0.0) for k in range(kmin, kmax + 1)]
        else:
            return [u for _, u in rows]

def load_u_from_json(path_or_inline: str) -> List[float]:
    """
    JSON formats accepted:
      - [u0, u1, u2, ...]
      - [{"u": 1.23}, {"u": 0.8}, ...]
      - {"vectors":[{"u":...}, ...]}
    """
    if not looks_inline_json(path_or_inline) and os.path.exists(path_or_inline):
        with open(path_or_inline) as f:
            data = json.load(f)
    else:
        data = json.loads(path_or_inline)

    if isinstance(data, list):
        out = []
        for item in data:
            out.append(float(item['u']) if isinstance(item, dict) else float(item))
        return out
    if isinstance(data, dict) and 'vectors' in data:
        return [float(x['u']) for x in data['vectors']]
    raise ValueError("JSON must be a list of numbers, a list of {'u':..}, or {'vectors':[...]}" )
