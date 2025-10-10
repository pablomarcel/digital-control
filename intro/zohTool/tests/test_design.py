from __future__ import annotations
import math
from intro.zohTool.design import CSVExporter, VCDWriter
from intro.zohTool.apis import IntervalEvent

def _evs_with_droop():
    # produce y1 != y0 to trigger the 'near t1' write path
    ev = IntervalEvent(k=0, t0=0.0, t1=1.0, u_in=1.0, y0=1.0, y1=math.exp(-1.0/2.0))
    return [ev]

def test_csv_exporter_writes(tmp_path):
    p = tmp_path / "out.csv"
    CSVExporter().write_results_csv(str(p), [IntervalEvent(0,0,1,0.5,0.5,0.5)], units="V")
    s = p.read_text()
    assert "u[V]" in s and "y1[V]" in s

def test_vcd_writer_with_idx_bits_and_droop(tmp_path):
    p = tmp_path / "sig.vcd"
    VCDWriter().write_vcd_zoh(str(p), _evs_with_droop(), scale=1e3, idx_bits=4)
    assert p.exists()
    txt = p.read_text()
    assert "$timescale 1ns" in txt
    assert "idx" in txt and "u_scaled" in txt and "y_scaled" in txt

def test_vcd_writer_empty_events(tmp_path):
    p = tmp_path / "empty.vcd"
    VCDWriter().write_vcd_zoh(str(p), [], scale=1.0, idx_bits=1)
    assert p.exists()
    assert "#0" not in p.read_text()
