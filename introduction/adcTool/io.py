
from __future__ import annotations
import csv, json, os
from typing import Iterable, Dict, Any, List

def load_vins_from_csv(path: str) -> Iterable[float]:
    with open(path, newline='') as f:
        rdr = csv.DictReader(f)
        if 'vin' not in rdr.fieldnames:
            raise ValueError("CSV must have a 'vin' column.")
        for row in rdr:
            yield float(row['vin'])

def load_vins_from_json(path_or_inline: str) -> Iterable[float]:
    if os.path.exists(path_or_inline):
        with open(path_or_inline) as f:
            data = json.load(f)
    else:
        data = json.loads(path_or_inline)

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                yield float(item['vin'])
            else:
                yield float(item)
    elif isinstance(data, dict) and 'vectors' in data:
        for item in data['vectors']:
            yield float(item['vin'])
    else:
        raise ValueError("JSON must be a list of numbers, list of {'vin':..}, or {'vectors':[...]}.")

def write_results_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    fields = [
        'index','vin','vin_clipped','nbits','vref','lsb','code',
        'vq_ideal','vdac_stop','e_ideal','e_effective','steps',
        'tconv_s','tconv_us','saturated'
    ]
    # some rows (SAR) don't have 'saturated' -> tolerate missing
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i, r in enumerate(rows):
            out = {k: r[k] for k in fields if k in r}
            out['index'] = i
            w.writerow(out)
