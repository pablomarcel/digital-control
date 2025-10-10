from __future__ import annotations
from typing import List, Dict, Any, Iterable
import random

try:
    import numpy as _np
    _HAS_NUMPY = True
except Exception:
    _HAS_NUMPY = False

def _solve_linear(G, I) -> List[float]:
    if _HAS_NUMPY:
        v = _np.linalg.solve(G, I)
        return [float(x) for x in v]
    # Tiny Gaussian elimination fallback
    n = len(I)
    A = [list(G[i]) + [I[i]] for i in range(n)]
    for k in range(n):
        piv = max(range(k, n), key=lambda r: abs(A[r][k]))
        A[k], A[piv] = A[piv], A[k]
        if abs(A[k][k]) < 1e-18:
            raise ValueError("Singular matrix")
        f = A[k][k]
        for c in range(k, n+1): A[k][c] /= f
        for r in range(k+1, n):
            f = A[r][k]
            for c in range(k, n+1):
                A[r][c] -= f * A[k][c]
    v = [0.0]*n
    for i in range(n-1, -1, -1):
        v[i] = A[i][n] - sum(A[i][j]*v[j] for j in range(i+1, n))
    return v

# --------------------------- Weighted DAC engine -------------------------------

def _weights_binary(nbits: int) -> List[float]:
    # LSB..MSB -> 1/2^{n-1}, ..., 1
    return [1.0 / (2.0**(nbits-1-i)) for i in range(nbits)]

class WeightedDAC:
    """Binary weighted-resistor DAC (summation DAC) ideal + simple mismatch model."""
    def __init__(self, nbits: int, vref: float, ro_over_r: float,
                 gain_err: float=0.0, vo_offset: float=0.0,
                 res_sigma_pct: float=0.0, seed: int|None=None):
        self.nbits = nbits
        self.vref = vref
        self.ro_over_r = ro_over_r
        self.gain_err = gain_err
        self.vo_offset = vo_offset
        self.base = _weights_binary(nbits)
        if res_sigma_pct > 0.0:
            rng = random.Random(seed)
            self.nonideal = [w * (1.0 + rng.gauss(0.0, res_sigma_pct/100.0)) for w in self.base]
        else:
            self.nonideal = self.base[:]

    def vo_ideal_bits(self, bits_lsb_first: List[int]) -> float:
        s = sum(bits_lsb_first[i]*self.base[i] for i in range(self.nbits))
        return self.ro_over_r * self.vref * s

    def vo_nonideal_bits(self, bits_lsb_first: List[int]) -> float:
        s = sum(bits_lsb_first[i]*self.nonideal[i] for i in range(self.nbits))
        return self.vo_offset + (1.0 + self.gain_err) * self.ro_over_r * self.vref * s

# ----------------------------- R-2R ladder engine ------------------------------

def _ideal_weights_r2r(nbits: int) -> List[float]:
    # LSB..MSB weights: [1/2^n, ..., 1/2]
    return [1.0 / (2.0 ** (nbits - i)) for i in range(1, nbits+1)]

def _build_G_for_ladder(nbits: int, R_vals: List[float], twoR_vals: List[float]):
    N = nbits + 1
    if _HAS_NUMPY:
        G = _np.zeros((N, N), dtype=float)
    else:
        G = [[0.0]*N for _ in range(N)]

    def stamp_series(a: int, b: int, R: float):
        g = 1.0 / float(R)
        if _HAS_NUMPY:
            G[a,a] += g; G[b,b] += g; G[a,b] -= g; G[b,a] -= g
        else:
            G[a][a] += g; G[b][b] += g; G[a][b] -= g; G[b][a] -= g

    def stamp_shunt(a: int, R: float):
        g = 1.0 / float(R)
        if _HAS_NUMPY: G[a,a] += g
        else:          G[a][a] += g

    for s in range(nbits):
        stamp_series(s, s+1, twoR_vals[s])
    stamp_shunt(nbits, twoR_vals[-1])
    for s in range(nbits):
        stamp_shunt(s, R_vals[s])

    return G

def _gen_R_values(nbits: int, R_nom: float, sigma_r_pct: float, seed=None) -> List[float]:
    rng = random.Random(seed)
    vals = []
    for _ in range(nbits):
        eps = rng.gauss(0.0, sigma_r_pct/100.0) if sigma_r_pct > 0 else 0.0
        vals.append(R_nom * (1.0 + eps))
    return vals

def _gen_2R_values(nbits: int, R_nom: float, sigma_2r_pct: float, seed=None) -> List[float]:
    rng = random.Random(None if seed is None else seed + 13)
    vals = []
    for _ in range(nbits + 1):
        eps = rng.gauss(0.0, sigma_2r_pct/100.0) if sigma_2r_pct > 0 else 0.0
        vals.append(2.0 * R_nom * (1.0 + eps))
    return vals

class R2RDAC:
    """Voltage-mode R-2R ladder DAC with nodal analysis and mismatch per resistor group."""
    def __init__(self, nbits: int, vref: float, R_ohm: float,
                 sigma_r_pct: float=0.0, sigma_2r_pct: float=0.0, seed: int|None=None,
                 gain_err: float=0.0, vo_offset: float=0.0):
        self.nbits = nbits
        self.vref = vref
        self.R_ohm = R_ohm
        self.sigma_r_pct = sigma_r_pct
        self.sigma_2r_pct = sigma_2r_pct
        self.seed = seed
        self.gain_err = gain_err
        self.vo_offset = vo_offset
        self._R_vals = _gen_R_values(nbits, R_ohm, sigma_r_pct, seed)
        self._2R_vals = _gen_2R_values(nbits, R_ohm, sigma_2r_pct, seed)
        self._w_ideal = _ideal_weights_r2r(nbits)  # LSB..MSB
        self._w_non = self._compute_nonideal_weights()

    def _compute_nonideal_weights(self) -> List[float]:
        G = _build_G_for_ladder(self.nbits, self._R_vals, self._2R_vals)
        N = self.nbits + 1
        msb_to_lsb = []
        for s in range(self.nbits):  # s=0 near OUT (MSB branch) ... s=n-1 (LSB)
            if _HAS_NUMPY:
                I = _np.zeros(N, dtype=float)
            else:
                I = [0.0]*N
            g_branch = 1.0 / float(self._R_vals[s])
            I[s] += g_branch * self.vref
            v = _solve_linear(G, I)
            msb_to_lsb.append(v[0] / self.vref)
        # Convert to LSB..MSB order expected by engines
        return list(reversed(msb_to_lsb))

    def vo_ideal_bits(self, bits_lsb_first: List[int]) -> float:
        s = sum(bits_lsb_first[k]*self._w_ideal[k] for k in range(self.nbits))
        return self.vref * s

    def vo_nonideal_bits(self, bits_lsb_first: List[int]) -> float:
        s = sum(bits_lsb_first[k]*self._w_non[k] for k in range(self.nbits))
        return self.vo_offset + (1.0 + self.gain_err) * s * self.vref
