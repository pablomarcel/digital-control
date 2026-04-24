
import os, json, numpy as np
from rst_controllers.rstTool.io import parse_coeffs, parse_complex_list, as_array, save_json_design, save_csv, load_json
from rst_controllers.rstTool.utils import pkg_out_path, pkg_in_path

def test_parse_and_paths(tmp_path, monkeypatch):
    # parse_coeffs handles spaces/commas and complex tokens
    arr = parse_coeffs("1, -2 3")
    assert np.allclose(arr, [1,-2,3])
    comps = parse_complex_list("0.5, -0.5j 1+2j")
    assert comps[1] == -0.5j and comps[2] == 1+2j

    # in/out paths
    outp = pkg_out_path("my.csv", "d.csv")
    assert outp.endswith("rst_controllers/rstTool/out/my.csv")
    inp = pkg_in_path("foo.json")
    assert inp.endswith("rst_controllers/rstTool/in/foo.json")

def test_save_and_load_json_and_csv(tmp_path):
    payload = {"hello": "world"}
    jpath = save_json_design("unit.json", payload)
    assert os.path.exists(jpath)
    # move to in/ and load
    in_dir = os.path.join("rst_controllers","rstTool","in")
    os.makedirs(in_dir, exist_ok=True)
    inp = os.path.join(in_dir, "unit.json")
    with open(jpath, "r") as f:
        data = f.read()
    with open(inp, "w") as f:
        f.write(data)
    loaded = load_json("unit.json")
    assert loaded["hello"] == "world"

    cpath = save_csv("unit.csv", [(0,1,2,3,4),(1,1,2,3,4)])
    assert os.path.exists(cpath)
