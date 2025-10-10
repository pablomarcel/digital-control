from __future__ import annotations
import os, csv
from intro.demuxTool.io import load_rows_from_csv, load_rows_from_json, write_results_csv, write_vcd
from intro.demuxTool.core import DemuxCircuit

def test_csv_and_json_load_and_writers(tmp_path):
    # Prepare CSV
    csvp = tmp_path / "v.csv"
    with open(csvp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["sel","x"])
        w.writeheader()
        w.writerow({"sel": 0, "x": 1})
        w.writerow({"sel": 1, "x": 3})
    rows_csv = list(load_rows_from_csv(str(csvp)))
    assert rows_csv == [{"sel":0,"x":1},{"sel":1,"x":3}]

    # Inline JSON
    inline = '[{"sel":2,"x":5},{"sel":1,"x":9}]'
    rows_json = list(load_rows_from_json(inline))
    assert rows_json == [{"sel":2,"x":5},{"sel":1,"x":9}]

    # Simulate and write outputs
    circ = DemuxCircuit(n_outputs=4, data_bw=8, strict=False)
    sim_rows = circ.simulate(rows_csv + rows_json)

    # Write results CSV
    out_csv = tmp_path / "out.csv"
    write_results_csv(str(out_csv), sim_rows, 4)
    assert out_csv.exists()
    # Write VCD
    out_vcd = tmp_path / "out.vcd"
    write_vcd(str(out_vcd), sim_rows, data_bw=8, n_outputs=4, sel_bits=circ.sel_bits)
    assert out_vcd.exists()

    # Basic VCD sanity: header tokens present
    txt = out_vcd.read_text()
    assert "$timescale" in txt and "$enddefinitions" in txt and "#0" in txt or "#10" in txt
