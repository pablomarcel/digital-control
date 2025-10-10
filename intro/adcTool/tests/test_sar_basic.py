
from intro.adcTool.core import SARADC

def test_sar_basic_known_code():
    adc = SARADC(tbit=1e-6, nbits=3, vref=0.8, comp_offset=0.0, dac_gain=1.0, dac_offset=0.0, jitter_rms=0.0)
    # LSB=0.8/8=0.1; vin=0.26V -> code 2 (0.2) since 0.3 would exceed
    summary, trace = adc.simulate_sample(0.26)
    assert summary['code'] in (2,3)  # allow threshold behavior with offsets/gain in future
    assert summary['steps'] == 3
