
import pytest
from introduction.muxTool.core import MuxCore

def test_mux_core_selects_inputs_correctly():
    core = MuxCore(data_bw=4)
    vecs = [
        {"sel": 0, "d0": 1, "d1": 2, "d2": 3, "d3": 4},
        {"sel": 1, "d0": 5, "d1": 6, "d2": 7, "d3": 8},
        {"sel": 2, "d0": 9, "d1": 10, "d2": 11, "d3": 12},
        {"sel": 3, "d0": 13, "d1": 14, "d2": 15, "d3": 0},
    ]
    out = core.simulate(vecs)
    assert [r["y"] for r in out] == [1, 6, 11, 0]
