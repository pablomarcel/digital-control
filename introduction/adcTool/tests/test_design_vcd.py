
from introduction.adcTool.design import write_vcd_counter, write_vcd_sar

def test_write_vcd_counter(tmp_path):
    # minimal synthetic trace: two steps, rising cmp on second
    trace = [
        {"time_s": 0.0, "step_idx": 0, "code":0, "vdac_err":0.0, "cmp":0},
        {"time_s": 1e-6, "step_idx": 1, "code":1, "vdac_err":0.1, "cmp":1},
    ]
    summary = {"code":1}  # not used by writer
    path = tmp_path / "c.vcd"
    last = write_vcd_counter(str(path), 4, summary, trace, all_mode=False)
    assert path.exists() and path.read_text().startswith("$date")
    assert isinstance(last, int)

def test_write_vcd_sar(tmp_path):
    trace = [
        {"time_s":0.0, "bit":2, "trial_code":4, "cmp":1, "latched_code":4, "vdac_trial":0.4},
        {"time_s":1e-6,"bit":1, "trial_code":6, "cmp":0, "latched_code":4, "vdac_trial":0.6},
        {"time_s":2e-6,"bit":0, "trial_code":5, "cmp":1, "latched_code":5, "vdac_trial":0.5},
    ]
    summary = {"code":5}
    path = tmp_path / "s.vcd"
    last = write_vcd_sar(str(path), 3, summary, trace, all_mode=False)
    txt = path.read_text()
    assert "$scope module sar_adc" in txt and "var wire 1 k clk" in txt
    assert isinstance(last, int)
