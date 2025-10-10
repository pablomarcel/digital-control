
from __future__ import annotations
from typing import Dict, Any, List

def _bin(v: int, w: int) -> str:
    return format(int(v) & ((1 << w) - 1), 'b').zfill(w)

def write_vcd_counter(path: str, nbits:int, summary: Dict[str, Any], trace: List[Dict[str, Any]], all_mode: bool=False, start_time_ns:int=0) -> int:
    def to_ns(tsec: float) -> int:
        return int(round(tsec * 1e9))
    events = []
    t0_ns = start_time_ns
    events.append((t0_ns, 'k', 1, '0'))
    if trace:
        events.append((t0_ns, 'c', nbits, _bin(trace[0]['code'], nbits)))
        events.append((t0_ns, 'p', 1, '0'))
    clk = 0
    for i in range(1, len(trace)):
        t_ns = start_time_ns + to_ns(trace[i]['time_s'])
        clk = 1 - clk
        events.append((t_ns, 'k', 1, '1' if clk else '0'))
        events.append((t_ns, 'c', nbits, _bin(trace[i]['code'], nbits)))
        if trace[i]['cmp'] != trace[i-1]['cmp']:
            events.append((t_ns, 'p', 1, '1' if trace[i]['cmp'] else '0'))
    if trace and trace[-1].get('cmp',0) == 1:
        t_end_ns = start_time_ns + to_ns(trace[-1]['time_s'])
        events.append((t_end_ns, 'p', 1, '1'))
    mode = 'a' if all_mode else 'w'
    with open(path, mode) as f:
        if not all_mode:
            f.write("$date\n    today\n$end\n")
            f.write("$version\n    adcTool-counter-vcd\n$end\n")
            f.write("$timescale 1ns $end\n")
            f.write("$scope module counter_adc $end\n")
            f.write(f"$var wire 1 k clk $end\n")
            f.write(f"$var wire 1 p cmp $end\n")
            f.write(f"$var wire {nbits} c code $end\n")
            f.write("$upscope $end\n$enddefinitions $end\n")
        last_t = None
        for (t_ns, name, width, value) in sorted(events, key=lambda e: e[0]):
            if last_t != t_ns:
                f.write(f"#{t_ns}\n")
                last_t = t_ns
            if width == 1:
                f.write(f"{value}{name}\n")
            else:
                f.write(f"b{value} {name}\n")
    return start_time_ns + (to_ns(trace[-1]['time_s']) if trace else 0)

def write_vcd_sar(path: str, nbits:int, summary: Dict[str, Any], trace: List[Dict[str, Any]], all_mode: bool=False, start_time_ns:int=0) -> int:
    def to_ns(tsec: float) -> int:
        return int(round(tsec * 1e9))
    w_i = max(1, (nbits-1).bit_length())
    events = []
    t0_ns = start_time_ns
    events.append((t0_ns, 'k', 1, '0'))
    if trace:
        events.append((t0_ns, 't', nbits, _bin(trace[0]['trial_code'], nbits)))
        events.append((t0_ns, 'c', nbits, _bin(trace[0]['latched_code'], nbits)))
        events.append((t0_ns, 'p', 1, '1' if trace[0]['cmp'] else '0'))
        events.append((t0_ns, 'i', w_i, _bin(trace[0]['bit'], w_i)))
    clk = 0
    for step in trace:
        t_ns = start_time_ns + to_ns(step['time_s'])
        clk = 1 - clk
        events.append((t_ns, 'k', 1, '1' if clk else '0'))
        events.append((t_ns, 't', nbits, _bin(step['trial_code'], nbits)))
        events.append((t_ns, 'c', nbits, _bin(step['latched_code'], nbits)))
        events.append((t_ns, 'p', 1, '1' if step['cmp'] else '0'))
        events.append((t_ns, 'i', w_i, _bin(step['bit'], w_i)))
    mode = 'a' if all_mode else 'w'
    with open(path, mode) as f:
        if not all_mode:
            f.write("$date\n    today\n$end\n")
            f.write("$version\n    adcTool-sar-vcd\n$end\n")
            f.write("$timescale 1ns $end\n")
            f.write("$scope module sar_adc $end\n")
            f.write(f"$var wire 1 k clk $end\n")
            f.write(f"$var wire 1 p cmp $end\n")
            f.write(f"$var wire {nbits} c code $end\n")
            f.write(f"$var wire {nbits} t trial $end\n")
            f.write(f"$var wire {w_i} i bit $end\n")
            f.write("$upscope $end\n$enddefinitions $end\n")
        last_t = None
        for (t, name, width, value) in sorted(events, key=lambda e: e[0]):
            if last_t != t:
                f.write(f"#{t}\n")
                last_t = t
            if width == 1:
                f.write(f"{value}{name}\n")
            else:
                f.write(f"b{value} {name}\n")
    return start_time_ns + (to_ns(trace[-1]['time_s']) if trace else 0)
