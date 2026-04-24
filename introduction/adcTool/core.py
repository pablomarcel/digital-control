
from __future__ import annotations
import math, random
from typing import Dict, Any, List, Tuple
try:
    import numpy as np  # optional for jitter
except Exception:
    np = None

class ADCBase:
    def __init__(self, nbits:int, vref:float, comp_offset:float=0.0, dac_gain:float=1.0, dac_offset:float=0.0, jitter_rms:float=0.0):
        self.nbits = nbits
        self.vref = vref
        self.comp_offset = comp_offset
        self.dac_gain = dac_gain
        self.dac_offset = dac_offset
        self.jitter_rms = jitter_rms

    def _gauss_dt(self, mean: float) -> float:
        jr = self.jitter_rms
        if jr <= 0.0:
            return mean
        if np is not None:
            return max(0.0, float(np.random.normal(loc=mean, scale=jr)))
        # fallback Box-Muller
        u1, u2 = random.random(), random.random()
        z = math.sqrt(-2.0 * math.log(max(u1, 1e-12))) * math.cos(2 * math.pi * u2)
        return max(0.0, mean + jr * z)

    def simulate_sample(self, vin: float) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        raise NotImplementedError

class CounterADC(ADCBase):
    def __init__(self, tclk: float, **kwargs):
        super().__init__(**kwargs)
        self.tclk = tclk

    def simulate_sample(self, vin: float) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        nbits = self.nbits; vref = self.vref
        nlevels = 1 << nbits
        q = vref / nlevels
        vin_clip = max(0.0, min(vin, vref - 1e-18))
        threshold = vin - self.comp_offset

        t = 0.0
        code = 0
        cmp_hit = False
        trace: List[Dict[str, Any]] = []

        for m in range(nlevels):
            vdac_err = self.dac_gain * (m * q) + self.dac_offset
            cmp_hit = (vdac_err >= threshold)
            trace.append({'time_s': t, 'step_idx': m, 'code': m, 'vdac_err': vdac_err, 'cmp': int(cmp_hit)})
            if cmp_hit:
                code = m
                break
            t += self._gauss_dt(self.tclk)

        if not cmp_hit:
            code = nlevels - 1
            vdac_err = self.dac_gain * (code * q) + self.dac_offset
            trace.append({'time_s': t, 'step_idx': code, 'code': code, 'vdac_err': vdac_err, 'cmp': 1})

        vq_ideal = code * q
        vdac_stop = self.dac_gain * (code * q) + self.dac_offset
        e_ideal = vin_clip - vq_ideal
        e_effective = vin - vdac_stop

        # total time from first to last entry (sum of deltas)
        tconv = sum(max(0.0, trace[i+1]['time_s'] - trace[i]['time_s']) for i in range(len(trace)-1))

        sat = (code == nlevels - 1) and (vin >= vref - 1e-18)

        summary = {
            'vin': vin, 'vin_clipped': vin_clip, 'nbits': nbits, 'vref': vref, 'lsb': q,
            'code': code, 'vq_ideal': vq_ideal, 'vdac_stop': vdac_stop,
            'e_ideal': e_ideal, 'e_effective': e_effective,
            'steps': trace[-1]['step_idx'] if trace else 0,
            'tconv_s': tconv, 'tconv_us': tconv * 1e6, 'saturated': int(sat),
            'params': {'tclk': self.tclk, 'comp_offset': self.comp_offset, 'dac_gain': self.dac_gain, 'dac_offset': self.dac_offset, 'jitter_rms': self.jitter_rms}
        }
        return summary, trace

class SARADC(ADCBase):
    def __init__(self, tbit: float, **kwargs):
        super().__init__(**kwargs)
        self.tbit = tbit

    def simulate_sample(self, vin: float) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        nbits = self.nbits; vref = self.vref
        nlevels = 1 << nbits
        Q = vref / nlevels
        vin_clip = max(0.0, min(vin, vref - 1e-18))
        vin_eff = vin - self.comp_offset

        code = 0
        t = 0.0
        trace: List[Dict[str, Any]] = []

        for b in reversed(range(nbits)):
            trial = code | (1 << b)
            vdac_trial = self.dac_gain * (trial * Q) + self.dac_offset
            cmp = 1 if vin_eff >= vdac_trial else 0
            latched = trial if cmp else code
            trace.append({'time_s': t, 'bit': b, 'trial_code': trial, 'cmp': cmp, 'latched_code': latched, 'vdac_trial': vdac_trial})
            code = latched
            t += self._gauss_dt(self.tbit)

        vq_ideal = code * Q
        e_ideal = vin_clip - vq_ideal
        vdac_stop = self.dac_gain * (code * Q) + self.dac_offset
        e_effective = vin - vdac_stop
        # zero-jitter exact time:
        tconv = (len(trace)) * self.tbit if self.jitter_rms == 0.0 else (trace[-1]['time_s'] - trace[0]['time_s'] + 0.0)

        summary = {
            'vin': vin, 'vin_clipped': vin_clip, 'nbits': nbits, 'vref': vref, 'lsb': Q,
            'code': code, 'vq_ideal': vq_ideal, 'vdac_stop': vdac_stop,
            'e_ideal': e_ideal, 'e_effective': e_effective,
            'steps': nbits, 'tconv_s': tconv, 'tconv_us': tconv * 1e6,
            'params': {'tbit': self.tbit, 'comp_offset': self.comp_offset, 'dac_gain': self.dac_gain, 'dac_offset': self.dac_offset, 'jitter_rms': self.jitter_rms}
        }
        return summary, trace

def make_engine(adc_type: str, **kwargs) -> ADCBase:
    if adc_type == "counter":
        return CounterADC(**kwargs)
    if adc_type == "sar":
        return SARADC(**kwargs)
    raise ValueError(f"Unknown adc_type: {adc_type}")
