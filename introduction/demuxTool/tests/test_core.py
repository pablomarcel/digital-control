from __future__ import annotations
import pytest
from introduction.demuxTool.core import DemuxCircuit

@pytest.mark.parametrize("N,bw", [(2, 4), (4, 8), (5, 8)])
def test_demux_shapes_and_basic_behaviour(N, bw):
    circ = DemuxCircuit(n_outputs=N, data_bw=bw, strict=False)
    # Vectors: walk sel, constant x
    xval = (1 << (bw - 1)) - 1
    vecs = [{"sel": i, "x": xval} for i in range(N)]
    rows = circ.simulate(vecs)
    assert len(rows) == N
    for i, r in enumerate(rows):
        # only one output non-zero; equals xval
        for k in range(N):
            exp = xval if k == i else 0
            assert r[f"y{k}"] == exp

def test_strict_invalid_sel_zeroes_all():
    """
    With strict=True:
      - sel is still masked to wire width and stored (here 7 -> 3 with 2 bits)
      - Outputs are explicitly zeroed when sel > N-1
    """
    circ = DemuxCircuit(n_outputs=3, data_bw=4, strict=True)  # N=3 -> sel_bits=2
    rows = circ.simulate([{"sel": 7, "x": 9}])  # 7 -> mask(7,2)=3; 3 > 2 -> zero outputs
    r = rows[0]
    assert r["sel"] == 3
    assert all(r[f"y{k}"] == 0 for k in range(3))

def test_invalid_sel_without_strict_is_zero_too():
    """
    With strict=False and N=3, sel=7 masks to 3 which doesn't match any y0..y2.
    So outputs are still all zero (no guard needed).
    """
    circ = DemuxCircuit(n_outputs=3, data_bw=4, strict=False)
    rows = circ.simulate([{"sel": 7, "x": 9}])
    r = rows[0]
    assert r["sel"] == 3
    assert all(r[f"y{k}"] == 0 for k in range(3))

def test_masks_x_to_bitwidth_and_routes_correctly():
    """
    x is masked to data_bw bits before routing.
    For data_bw=4, x=0x3F -> 0xF.
    """
    circ = DemuxCircuit(n_outputs=2, data_bw=4, strict=False)
    rows = circ.simulate([{"sel": 1, "x": 0x3F}])  # masked x -> 0xF
    r = rows[0]
    assert r["x"] == 0xF
    assert r["y0"] == 0
    assert r["y1"] == 0xF
