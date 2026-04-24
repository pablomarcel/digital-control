
from __future__ import annotations
import csv, json, os
from typing import Dict, Iterable, Iterator, List
from .utils import resolve_input_path, resolve_output_path, mask, ensure_dir

def load_rows_from_csv(path: str) -> Iterator[Dict[str,int]]:
    with open(path, newline='') as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            yield {k: int(row[k], 0) if isinstance(row[k], str) else int(row[k]) for k in row}

def load_rows_from_json(path_or_inline: str) -> Iterator[Dict[str,int]]:
    if os.path.exists(path_or_inline):
        with open(path_or_inline) as f:
            data = json.load(f)
    else:
        data = json.loads(path_or_inline)
    if isinstance(data, dict) and 'vectors' in data:
        data = data['vectors']
    for row in data:
        yield {k: int(row[k]) for k in row}

def write_results_csv(filename: str, rows: List[Dict[str,int]]) -> None:
    ensure_dir(filename)
    with open(filename, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['cycle','sel','d0','d1','d2','d3','y'])
        w.writeheader(); w.writerows(rows)
