import os, csv
from introduction.vcdTool.io import resolve_input_path, resolve_output_path, export_csv, unit_scale_map, timescale_map

def test_resolve_input_path_relative(tmp_path):
    # create a file under in_dir
    (tmp_path / "in").mkdir()
    p = tmp_path / "in" / "a.vcd"
    p.write_text("")
    got = resolve_input_path("a.vcd", str(tmp_path / "in"))
    assert got == str(p)

def test_resolve_output_path_creates_dir(tmp_path):
    out = resolve_output_path("sub/out.csv", str(tmp_path))
    # Path should be under tmp_path/sub/out.csv
    assert out == os.path.join(str(tmp_path), "sub", "out.csv")
    # Dir should exist
    assert os.path.isdir(os.path.join(str(tmp_path), "sub"))

def test_export_csv_and_maps(tmp_path):
    csv_path = os.path.join(str(tmp_path), "t.csv")
    export_csv(csv_path, [0.0, 1.0], {"a":[0,1], "b":[1,2]}, "s")
    with open(csv_path) as f:
        rows = list(csv.reader(f))
    assert rows[0][0].startswith("time_")
    assert rows[1] == ["0", "0", "1"]
    assert "us" in unit_scale_map()
    assert "ns" in timescale_map()
