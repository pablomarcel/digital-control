
from __future__ import annotations
from typing import List, Dict
from .utils import ensure_dir

def _bin(v: int, w: int) -> str:
    return format(int(v) & ((1 << w) - 1), 'b').zfill(w)

def write_vcd(filename: str, rows: List[Dict[str,int]], data_bw: int, timescale: str='1ns') -> None:
    """
    Minimal VCD writer for signals: sel (2 bits), d0..d3 (data_bw), y (data_bw).
    One timestamp per cycle (10 ns apart).
    """
    ensure_dir(filename)
    signals = [
        ('s', 'sel', 2),
        ('a', 'd0',  data_bw),
        ('b', 'd1',  data_bw),
        ('c', 'd2',  data_bw),
        ('d', 'd3',  data_bw),
        ('y', 'y',   data_bw),
    ]
    with open(filename, 'w') as f:
        f.write("$date\n    today\n$end\n")
        f.write(f"$version\n    muxTool-vcd-writer\n$end\n")
        f.write(f"$timescale {timescale} $end\n")
        f.write("$scope module mux $end\n")
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

        prev = {}
        for i, r in enumerate(rows):
            t = i * 10
            f.write(f"#{t}\n")
            for sym, name, width in signals:
                val = _bin(r[name], width)
                if prev.get(name) != val:
                    f.write(f"b{val} {sym}\n")
                    prev[name] = val
