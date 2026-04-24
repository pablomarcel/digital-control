from __future__ import annotations
import csv, json, os
from typing import Dict, Iterable, Iterator, List
from .utils import looks_inline_json

def load_rows_from_csv(path: str) -> Iterator[Dict[str,int]]:
    with open(path, newline='') as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            def to_int(k):
                v = row[k]
                return int(v, 0) if isinstance(v, str) else int(v)
            yield {'sel': to_int('sel'), 'x': to_int('x')}

def load_rows_from_json(path_or_inline: str) -> Iterator[Dict[str,int]]:
    if not looks_inline_json(path_or_inline) and os.path.exists(path_or_inline):
        with open(path_or_inline) as f:
            data = json.load(f)
    else:
        data = json.loads(path_or_inline)
    if isinstance(data, dict) and 'vectors' in data:
        data = data['vectors']
    for row in data:
        yield {'sel': int(row['sel']), 'x': int(row['x'])}

def write_results_csv(filename: str, rows: List[Dict[str,int]], n_outputs: int) -> None:
    fieldnames = ['cycle', 'sel', 'x'] + [f'y{k}' for k in range(n_outputs)]
    with open(filename, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader(); w.writerows(rows)

# ----------------------------- VCD writer -------------------------------------
def _bin(v, w):  # zero-padded binary
    return format(int(v) & ((1 << w) - 1), 'b').zfill(w)

def write_vcd(filename: str, rows: List[Dict[str,int]], data_bw: int, n_outputs: int, sel_bits: int, timescale: str='1ns') -> None:
    signals = [('s', 'sel', sel_bits), ('x', 'x', data_bw)]
    # Simple symbol IDs for y0..yN-1
    id_letters = [chr(o) for o in range(ord('a'), ord('z')+1)]
    for i in range(n_outputs):
        sym = id_letters[i] if i < len(id_letters) else f'Y{i}'
        signals.append((sym, f'y{i}', data_bw))

    with open(filename, 'w') as f:
        f.write("$date\n    today\n$end\n")
        f.write(f"$version\n    demux-vcd-writer\n$end\n")
        f.write(f"$timescale {timescale} $end\n")
        f.write("$scope module demux $end\n")
        for sym, name, width in signals:
            f.write(f"$var wire {width} {sym} {name} $end\n")
        f.write("$upscope $end\n$enddefinitions $end\n")

        # Initial dump
        f.write("$dumpvars\n")
        if rows:
            r0 = rows[0]
            for sym, name, width in signals:
                f.write(f"b{_bin(r0[name], width)} {sym}\n")
        f.write("$end\n")

        # Changes per cycle (10 ns apart)
        prev = {}
        for i, r in enumerate(rows):
            t = i * 10
            f.write(f"#{t}\n")
            for sym, name, width in signals:
                val = _bin(r[name], width)
                if prev.get(name) != val:
                    f.write(f"b{val} {sym}\n")
                    prev[name] = val
