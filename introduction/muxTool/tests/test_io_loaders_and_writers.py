
import csv, json, os
from introduction.muxTool.io import load_rows_from_csv, load_rows_from_json, write_results_csv

def test_load_rows_from_csv(tmp_path):
    p = tmp_path / "v.csv"
    p.write_text("sel,d0,d1,d2,d3\n0,1,2,3,4\n1,5,6,7,8\n")
    rows = list(load_rows_from_csv(str(p)))
    assert rows[0]["sel"] == 0 and rows[1]["d2"] == 7

def test_load_rows_from_json_file_and_inline(tmp_path):
    pf = tmp_path / "v.json"
    pf.write_text(json.dumps([{"sel":0,"d0":1,"d1":2,"d2":3,"d3":4}]))
    rows_file = list(load_rows_from_json(str(pf)))
    assert rows_file[0]["d3"] == 4

    inline = json.dumps({"vectors":[{"sel":1,"d0":5,"d1":6,"d2":7,"d3":8}]})
    rows_inline = list(load_rows_from_json(inline))
    assert rows_inline[0]["sel"] == 1 and rows_inline[0]["d2"] == 7

def test_write_results_csv(tmp_path):
    out = tmp_path / "r" / "results.csv"
    rows = [{"cycle":0,"sel":0,"d0":1,"d1":2,"d2":3,"d3":4,"y":1},
            {"cycle":1,"sel":1,"d0":5,"d1":6,"d2":7,"d3":8,"y":6}]
    write_results_csv(str(out), rows)
    assert out.exists()
    content = out.read_text().splitlines()
    assert content[0].startswith("cycle,sel,d0,d1,d2,d3,y")
