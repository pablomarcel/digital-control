
from __future__ import annotations
from typing import Dict, List
import pyrtl as rtl
from .utils import mask, log_call

class MuxCore:
    """Core 4:1 mux built with PyRTL. y = mux(sel, d0, d1, d2, d3)."""
    def __init__(self, data_bw: int = 8):
        self.data_bw = int(data_bw)
        self.ports = {}

    @log_call
    def build(self) -> Dict[str, rtl.WireVector]:
        rtl.reset_working_block()
        sel = rtl.Input(2, 'sel')
        d0  = rtl.Input(self.data_bw, 'd0')
        d1  = rtl.Input(self.data_bw, 'd1')
        d2  = rtl.Input(self.data_bw, 'd2')
        d3  = rtl.Input(self.data_bw, 'd3')
        y   = rtl.Output(self.data_bw, 'y')
        y <<= rtl.mux(sel, d0, d1, d2, d3)
        self.ports = {'sel': sel, 'd0': d0, 'd1': d1, 'd2': d2, 'd3': d3, 'y': y}
        return self.ports

    @log_call
    def simulate(self, vectors: List[Dict[str,int]]) -> List[Dict[str,int]]:
        if not self.ports:
            self.build()
        sim = rtl.Simulation()
        out_rows = []
        for i, row in enumerate(vectors):
            provided = {
                'sel': mask(row['sel'], 2),
                'd0':  mask(row['d0'], self.data_bw),
                'd1':  mask(row['d1'], self.data_bw),
                'd2':  mask(row['d2'], self.data_bw),
                'd3':  mask(row['d3'], self.data_bw),
            }
            sim.step(provided_inputs=provided)
            y = sim.inspect('y')
            out = {'cycle': i, **provided, 'y': int(y)}
            out_rows.append(out)
        return out_rows
