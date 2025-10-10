
import csv, json, os
from intro.adcTool.app import ADCApp
from intro.adcTool.apis import RunRequest

def _write_csv(path, vals):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["vin"])
        w.writeheader()
        for v in vals:
            w.writerow({"vin": v})

def test_app_counter_and_sar_end_to_end(tmp_path, capsys):
    # inputs/outputs
    in_dir = tmp_path / "in"; out_dir = tmp_path / "out"
    in_dir.mkdir(); out_dir.mkdir()
    csv_path = in_dir / "vins.csv"
    _write_csv(csv_path, [0.05, 0.15, 0.25])
    json_path = in_dir / "vins.json"
    json_path.write_text(json.dumps([0.05, 0.15, 0.25]))

    # Counter run
    app = ADCApp()
    req_c = RunRequest(
        adc_type="counter", csv=str(csv_path), nbits=4, vref=1.6, tclk=1e-6,
        in_dir=str(in_dir), out_dir=str(out_dir),
        out_csv="c_results.csv", trace_vcd="last.vcd", trace_all_vcd="all.vcd",
        radix="all"
    )
    res_c = app.run(req_c)
    assert res_c.wrote_csv and os.path.exists(res_c.wrote_csv)
    assert res_c.wrote_vcd and os.path.exists(res_c.wrote_vcd)
    assert res_c.wrote_vcd_all and os.path.exists(res_c.wrote_vcd_all)

    # SAR run (from JSON)
    req_s = RunRequest(
        adc_type="sar", json=str(json_path), nbits=4, vref=1.6, tbit=2e-6,
        in_dir=str(in_dir), out_dir=str(out_dir),
        out_csv="s_results.csv", trace_vcd="s_last.vcd", trace_all_vcd="s_all.vcd"
    )
    res_s = app.run(req_s)
    assert res_s.wrote_csv and os.path.exists(res_s.wrote_csv)

    # stdout contained formatted code lines
    out = capsys.readouterr().out
    assert "vin=" in out and "code=" in out
