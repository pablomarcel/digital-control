
from __future__ import annotations
from typing import List

def parse_coeffs(vals: List[str]) -> List[float]:
    """Parse list of numbers, respecting Python literals (e.g., 1e-3)."""
    return [float(eval(v)) for v in vals]

def parse_complex_list(vals: List[str]):
    """Parse list like ['0.8','0.7+0.2j','0.7-0.2j'] into complex numbers."""
    return [complex(eval(v)) for v in vals]
