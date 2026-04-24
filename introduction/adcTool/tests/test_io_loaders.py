
import json, csv, os
from introduction.adcTool.io import load_vins_from_csv, load_vins_from_json, write_results_csv

def test_load_csv_and_json(tmp_path):
    # CSV
    csv_path = tmp_path / "vins.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["vin"])
        w.writeheader()
        for v in [0.1, 0.2, 0.3]:
            w.writerow({"vin": v})
    vals_csv = list(load_vins_from_csv(str(csv_path)))
    assert vals_csv == [0.1, 0.2, 0.3]

    # JSON: list of numbers
    j1 = tmp_path / "v1.json"
    j1.write_text(json.dumps([0.11, 0.22]))
    assert list(load_vins_from_json(str(j1))) == [0.11, 0.22]

    # JSON: list of dicts
    j2 = tmp_path / "v2.json"
    j2.write_text(json.dumps([{"vin":0.5},{"vin":0.7}]))
    assert list(load_vins_from_json(str(j2))) == [0.5, 0.7]

    # JSON: {'vectors': [...]}
    j3 = tmp_path / "v3.json"
    j3.write_text(json.dumps({"vectors":[{"vin":1.1},{"vin":1.3}]}))
    assert list(load_vins_from_json(str(j3))) == [1.1, 1.3]

def test_write_results_csv(tmp_path):
    out = tmp_path / "res.csv"
    rows = [
        {"vin":0.1,"vin_clipped":0.1,"nbits":4,"vref":1.6,"lsb":0.1,"code":1,"vq_ideal":0.1,
         "vdac_stop":0.1,"e_ideal":0.0,"e_effective":0.0,"steps":1,"tconv_s":1e-6,"tconv_us":1.0,"saturated":0},
        {"vin":0.2,"vin_clipped":0.2,"nbits":4,"vref":1.6,"lsb":0.1,"code":2,"vq_ideal":0.2,
         "vdac_stop":0.2,"e_ideal":0.0,"e_effective":0.0,"steps":2,"tconv_s":2e-6,"tconv_us":2.0,"saturated":0},
    ]
    write_results_csv(str(out), rows)
    assert out.exists()
    txt = out.read_text()
    assert "index,vin,vin_clipped" in txt and "code" in txt
