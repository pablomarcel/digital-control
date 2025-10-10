from __future__ import annotations
import csv
from typing import List, Dict, Any
from .apis import Update
from .utils import bin_zero_padded

def write_results_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    # Union of both DAC types' fields (missing ones left blank)
    fields = [
        'index','nbits','vref','R_ohm','sigma_r_pct','sigma_2r_pct',
        'ro_over_r','res_sigma_pct','code',
        'vo_ideal','vo_nonideal','error','gain_err','vo_offset'
    ]
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i, r in enumerate(rows):
            out = {k: r.get(k, '') for k in fields}
            out['index'] = i
            w.writerow(out)

def write_vcd(path: str,
              nbits: int,
              updates: List[Update],
              tupd: float,
              start_time_ns: int = 0,
              all_mode: bool = False,
              include_ideal: bool = False) -> int:
    """Generic VCD writer used by both engines; values in microvolts."""
    def to_ns(tsec: float) -> int:
        return int(round(tsec * 1e9))

    events = []
    clk = 0
    t_ns = start_time_ns
    events.append((t_ns, 'k', 1, '0'))

    for upd in updates:
        code   = upd.code
        vo_uV  = int(round(upd.vo_nonideal * 1e6))
        voi_uV = int(round(upd.vo_ideal   * 1e6))
        events.append((t_ns, 'c',  nbits, bin_zero_padded(code, nbits, 0)))
        events.append((t_ns, 'v',  32,    bin_zero_padded(vo_uV, 32, 0)))
        if include_ideal:
            events.append((t_ns, 'vi', 32, bin_zero_padded(voi_uV, 32, 0)))
        clk = 1 - clk
        events.append((t_ns, 'k', 1, '1' if clk else '0'))
        t_ns += to_ns(tupd)

    mode = 'a' if all_mode else 'w'
    with open(path, mode) as f:
        if not all_mode:
            f.write("$date\n    today\n$end\n")
            f.write("$version\n    dacTool-vcd\n$end\n")
            f.write("$timescale 1ns $end\n")
            f.write("$scope module dacTool $end\n")
            f.write(f"$var wire 1 k clk $end\n")
            f.write(f"$var wire {nbits} c code $end\n")
            f.write(f"$var wire 32 v vo_uV $end\n")
            if include_ideal:
                f.write(f"$var wire 32 vi voi_uV $end\n")
            f.write("$upscope $end\n$enddefinitions $end\n")

        last_t = None
        for (t, name, width, value) in events:
            if last_t != t:
                f.write(f"#{t}\n")
                last_t = t
            if width == 1:
                f.write(f"{value}{name}\n")
            else:
                f.write(f"b{value} {name}\n")
    return t_ns
