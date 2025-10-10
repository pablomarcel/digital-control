
from intro.adcTool.core import CounterADC

def test_counter_basic_midscale():
    adc = CounterADC(tclk=1e-6, nbits=4, vref=1.6, comp_offset=0.0, dac_gain=1.0, dac_offset=0.0, jitter_rms=0.0)
    # LSB = 1.6/16 = 0.1; vin=0.35V should give code 3 (0.3V) or 4 (0.4V) depending on ramp policy.
    summary, trace = adc.simulate_sample(0.35)
    assert 0 <= summary['code'] < (1<<4)
    assert abs(summary['vq_ideal'] - summary['code']*0.1) < 1e-12
    assert summary['tconv_s'] >= 0.0
