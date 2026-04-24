from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple
import re, math
from collections import namedtuple

from .io import timescale_map, unit_scale_map

Var = namedtuple('Var', 'id name width')

@dataclass
class VCDData:
    timescale_factor: float
    vars_by_id: Dict[str, Var]
    events: List[Tuple[int, List[Tuple[str, str]]]]

class VCDParser:
    def parse(self, path: str) -> VCDData:
        _TS_MULT = timescale_map()
        vars_by_id: Dict[str, Var] = {}
        events: List[Tuple[int, List[Tuple[str,str]]]] = []
        timescale_factor = 1e-9
        cur_time = 0

        var_re = re.compile(r'^\$var\s+\w+\s+(\d+)\s+(\S+)\s+(\S+)\s+\$end')
        ts_re  = re.compile(r'^\$timescale\s+(\d+)\s*(s|ms|us|ns|ps|fs)\s*\$end', re.IGNORECASE)

        with open(path,'r',errors='ignore') as f:
            in_header = True
            for raw in f:
                line = raw.strip()
                if not line:
                    continue
                if in_header:
                    if line.startswith('$var'):
                        m = var_re.match(line)
                        if m:
                            width  = int(m.group(1))
                            var_id = m.group(2)
                            name   = m.group(3)
                            vars_by_id[var_id] = Var(var_id, name, width)
                    elif line.lower().startswith('$timescale'):
                        norm = (line
                                .replace('PS','ps').replace('NS','ns').replace('US','us')
                                .replace('MS','ms').replace('FS','fs').replace('S','s'))
                        m = ts_re.match(norm)
                        if m:
                            num = int(m.group(1)); unit = m.group(2).lower()
                            timescale_factor = num * _TS_MULT[unit]
                    elif line == '$enddefinitions $end':
                        in_header = False
                    continue
                if line[0] == '#':
                    cur_time = int(line[1:])
                    events.append((cur_time, []))
                elif line[0] in ('0','1','x','z'):
                    val = line[0]; var_id = line[1:]
                    if not events: events.append((cur_time, []))
                    events[-1][1].append((var_id, val))
                elif line[0] in ('b','B'):
                    parts = line.split()
                    if len(parts) == 2:
                        bits, var_id = parts
                        val = 'b' + bits[1:]
                        if not events: events.append((cur_time, []))
                        events[-1][1].append((var_id, val))
            # filter empties except t=0
        events = [(t,ch) for (t,ch) in events if ch or t == 0]
        return VCDData(timescale_factor, vars_by_id, events)

class WaveformBuilder:
    def build(self, vcd: VCDData, wanted_names: List[str]):
        id_by_name = {v.name: vid for vid, v in vcd.vars_by_id.items()}
        missing = [n for n in wanted_names if n not in id_by_name]
        if missing:
            avail = ", ".join(sorted(id_by_name.keys()))
            raise ValueError(f"Signals not found in VCD: {missing}\nAvailable: {avail}")
        cur: Dict[str,str] = {}
        widths: Dict[str,int] = {}
        for n in wanted_names:
            vid = id_by_name[n];
            w = vcd.vars_by_id[vid].width
            widths[n] = w
            cur[n] = '0' if w == 1 else ('b' + '0'*w)
        times: List[int] = []
        rawbits = {n: [] for n in wanted_names}
        for t,changes in vcd.events:
            for vid,val in changes:
                v = vcd.vars_by_id.get(vid)
                if not v: continue
                name = v.name
                if name in cur:
                    if val in ('0','1'):
                        cur[name] = val
                    elif val.startswith('b'):
                        bits = val[1:]
                        if len(bits) < v.width:
                            bits = bits.zfill(v.width)
                        cur[name] = 'b' + bits
            times.append(t)
            for n in wanted_names:
                rawbits[n].append(cur[n])
        series: Dict[str, List[float]] = {}
        for n in wanted_names:
            nums: List[float] = []
            for rb in rawbits[n]:
                if rb in ('0','1'):
                    nums.append(1 if rb == '1' else 0)
                elif isinstance(rb, str) and rb.startswith('b'):
                    try:
                        nums.append(int(rb[1:], 2))
                    except ValueError:
                        nums.append(math.nan)
                else:
                    nums.append(math.nan)
            series[n] = nums
        return times, series, rawbits, widths

class Decoder:
    def apply(self, series, rawbits, widths, decodes: List[Tuple[str,int]]):
        for bus, nbits in decodes:
            if bus not in series:
                print(f"[warn] --decode ignored: '{bus}' not in current signals; add it to --signals.")
                continue
            vals = series[bus]; rb = rawbits[bus]
            for i in reversed(range(nbits)):  # MSB..LSB
                name = f"{bus}[{i}]"
                bit_series, bit_raw = [], []
                for j in range(len(vals)):
                    if isinstance(rb[j], str) and rb[j].startswith('b') and len(rb[j]) >= 2:
                        bstr = rb[j][1:].zfill(nbits)
                        b = bstr[-(i+1)]
                        bit_raw.append(b)
                        bit_series.append(int(b)) if b in ('0','1') else bit_series.append(math.nan)
                    else:
                        v = vals[j]
                        if isinstance(v, float) and math.isnan(v):
                            bit_series.append(math.nan); bit_raw.append('x')
                        else:
                            iv = int(v)
                            bit_series.append((iv >> i) & 1)
                            bit_raw.append('1' if ((iv >> i) & 1) else '0')
                series[name] = bit_series; rawbits[name] = bit_raw; widths[name] = 1
