from __future__ import annotations
import csv
from typing import List, Optional
from .apis import IntervalEvent
from .utils import ensure_dir

def _bin(width: int, value: int) -> str:
    return format(value & ((1 << width) - 1), 'b').zfill(width)

class CSVExporter:
    def write_results_csv(self, path: str, events: List[IntervalEvent], units: str) -> None:
        ensure_dir(path)
        with open(path, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['k','t0_s','t1_s',f'u[{units}]',f'y0[{units}]',f'y1[{units}]'])
            for ev in events:
                w.writerow([ev.k, f"{ev.t0:.12g}", f"{ev.t1:.12g}", f"{ev.u_in:.12g}", f"{ev.y0:.12g}", f"{ev.y1:.12g}"])

class VCDWriter:
    def write_vcd_zoh(self, path: str, events: List[IntervalEvent], scale: float = 1e6, idx_bits: Optional[int] = None) -> None:
        ensure_dir(path)

        def ns(tsec: float) -> int:
            return int(round(tsec * 1e9))

        if idx_bits is None:
            max_k = max(ev.k for ev in events) if events else 0
            idx_bits = max(1, (max_k or 1).bit_length())

        with open(path, 'w') as f:
            f.write("$date\n    today\n$end\n")
            f.write("$version\n    zoh-vcd\n$end\n")
            f.write("$timescale 1ns $end\n")
            f.write("$scope module zoh $end\n")
            f.write("$var wire 1 k clk $end\n")
            f.write(f"$var wire {idx_bits} i idx $end\n")
            f.write("$var wire 32 u u_scaled $end\n")
            f.write("$var wire 32 y y_scaled $end\n")
            f.write("$upscope $end\n$enddefinitions $end\n")

            tprev = -1
            clk = 0

            for ev in events:
                # BEGIN interval at t0
                t0 = ns(ev.t0)
                if t0 != tprev:
                    f.write(f"#{t0}\n")
                    tprev = t0
                clk ^= 1
                f.write(f"{clk}k\n")
                f.write(f"b{_bin(idx_bits, ev.k)} i\n")

                u_scaled = int(round(max(0.0, ev.u_in * scale)))
                y0_scaled = int(round(max(0.0, ev.y0 * scale)))
                f.write(f"b{_bin(32, u_scaled)} u\n")
                f.write(f"b{_bin(32, y0_scaled)} y\n")

                # If droop is modeled (y1 != y0), add a point just before t1
                if abs(ev.y1 - ev.y0) > 1e-18:
                    t1m = max(t0, ns(ev.t1) - 1)  # one nanosecond before t1
                    if t1m != tprev:
                        f.write(f"#{t1m}\n")
                        tprev = t1m
                    y1_scaled = int(round(max(0.0, ev.y1 * scale)))
                    f.write(f"b{_bin(32, y1_scaled)} y\n")

            # final timestamp at the very end for completeness
            if events:
                tend = ns(events[-1].t1)
                if tend != tprev:
                    f.write(f"#{tend}\n")
