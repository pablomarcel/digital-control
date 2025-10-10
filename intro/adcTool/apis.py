
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, List, Dict, Any

ADCType = Literal["counter", "sar"]

@dataclass
class RunRequest:
    adc_type: ADCType
    # input selection (exactly one): csv or json (file path or inline JSON for json)
    csv: str | None = None
    json: str | None = None

    # common parameters
    nbits: int = 10
    vref: float = 3.3
    comp_offset: float = 0.0
    dac_gain: float = 1.0
    dac_offset: float = 0.0
    jitter_rms: float = 0.0
    radix: str = "dec"

    # timing (choose based on adc_type)
    tclk: float = 1e-6      # used by counter
    tbit: float = 1e-6      # used by SAR

    # dir policy
    in_dir: str = "in"
    out_dir: str = "out"

    # outputs
    out_csv: str | None = None
    trace_vcd: str | None = None
    trace_all_vcd: str | None = None

@dataclass
class SampleSummary:
    data: Dict[str, Any]

@dataclass
class RunResult:
    results: List[SampleSummary] = field(default_factory=list)
    wrote_csv: str | None = None
    wrote_vcd: str | None = None
    wrote_vcd_all: str | None = None
