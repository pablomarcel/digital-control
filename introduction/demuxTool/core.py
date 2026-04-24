from __future__ import annotations
import math
from typing import Dict, List
import pyrtl as rtl
from .utils import mask

class DemuxCircuit:
    """Combinational N-way demultiplexer built in PyRTL.

    Ports:
      inputs:  sel (log2 N bits), x (data_bw bits)
      outputs: y0..y{N-1} (each data_bw bits)
    Behavior: y[i] = x if sel==i else 0.
    """
    def __init__(self, n_outputs: int=4, data_bw: int=8, strict: bool=False):
        assert n_outputs >= 2, "n_outputs must be >= 2"
        self.n_outputs = int(n_outputs)
        self.data_bw = int(data_bw)
        self.strict = bool(strict)
        self.sel_bits = max(1, int(math.ceil(math.log2(self.n_outputs))))
        self.ports = None  # filled in by build()

    def build(self) -> Dict[str, object]:
        rtl.reset_working_block()
        sel = rtl.Input(self.sel_bits, 'sel')
        x   = rtl.Input(self.data_bw, 'x')

        max_code = rtl.Const(self.n_outputs - 1, bitwidth=self.sel_bits)
        valid = sel <= max_code
        ys = []
        zero = rtl.Const(0, bitwidth=self.data_bw)
        for i in range(self.n_outputs):
            y = rtl.Output(self.data_bw, f'y{i}')
            eq = (sel == rtl.Const(i, bitwidth=self.sel_bits))
            pred = (eq & valid) if self.strict else eq
            y <<= rtl.select(pred, x, zero)
            ys.append(y)
        self.ports = {'sel': sel, 'x': x, 'ys': ys}
        return self.ports

    def simulate(self, vectors: List[Dict[str,int]]) -> List[Dict[str,int]]:
        if self.ports is None:
            self.build()
        sim = rtl.Simulation()
        out_rows: List[Dict[str,int]] = []
        for i, row in enumerate(vectors):
            sel_raw = int(row['sel'])
            x_raw   = int(row['x'])
            sel = mask(sel_raw, self.sel_bits)
            x   = mask(x_raw, self.data_bw)
            sim.step(provided_inputs={'sel': sel, 'x': x})
            record = {'cycle': i, 'sel': sel, 'x': x}
            for k in range(self.n_outputs):
                record[f'y{k}'] = sim.inspect(f'y{k}')
            out_rows.append(record)
        return out_rows
