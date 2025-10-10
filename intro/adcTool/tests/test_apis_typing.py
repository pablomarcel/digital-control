
from intro.adcTool.apis import RunRequest

def test_runrequest_defaults_and_types():
    r = RunRequest(adc_type="sar", json="[0.1,0.2]")
    assert r.nbits == 10 and r.vref == 3.3
    assert r.adc_type == "sar"
    # ensure timing fields exist
    assert hasattr(r, "tbit") and hasattr(r, "tclk")
    # dir policy defaults
    assert r.in_dir == "in" and r.out_dir == "out"
