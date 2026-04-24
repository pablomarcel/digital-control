
from __future__ import annotations
from typing import List, Dict, Any
from .apis import RunRequest, RunResult, SampleSummary
from .utils import resolve_input_path, resolve_output_path, fmt_code
from .io import load_vins_from_csv, load_vins_from_json, write_results_csv
from .core import make_engine
from .design import write_vcd_counter, write_vcd_sar

class ADCApp:
    def run(self, req: RunRequest) -> RunResult:
        # resolve paths
        csv_path  = resolve_input_path(req.csv,  req.in_dir)  if req.csv  else None
        json_spec = resolve_input_path(req.json, req.in_dir)  if req.json else None
        out_csv   = resolve_output_path(req.out_csv,       req.out_dir) if req.out_csv       else None
        out_vcd   = resolve_output_path(req.trace_vcd,     req.out_dir) if req.trace_vcd     else None
        out_vcd_all = resolve_output_path(req.trace_all_vcd, req.out_dir) if req.trace_all_vcd else None

        # load inputs
        if csv_path:
            vins = list(load_vins_from_csv(csv_path))
        else:
            vins = list(load_vins_from_json(json_spec)) if json_spec else []

        engine_kwargs = dict(nbits=req.nbits, vref=req.vref, comp_offset=req.comp_offset, dac_gain=req.dac_gain, dac_offset=req.dac_offset, jitter_rms=req.jitter_rms)
        if req.adc_type == "counter":
            engine = make_engine("counter", tclk=req.tclk, **engine_kwargs)
        else:
            engine = make_engine("sar", tbit=req.tbit, **engine_kwargs)

        results: List[SampleSummary] = []
        last_time_ns = 0

        for i, vin in enumerate(vins):
            summary, trace = engine.simulate_sample(vin)
            results.append(SampleSummary(summary))

            code_str = fmt_code(summary['code'], req.nbits, req.radix)
            print(f"[{i}] vin={summary['vin']:.6g} V  -> code={code_str}  vq={summary['vq_ideal']:.6g} V  e={summary['e_ideal']:.6g} V  Tconv={summary['tconv_us']:.3f} us")

            if out_vcd and i == len(vins) - 1:
                if req.adc_type == "counter":
                    write_vcd_counter(out_vcd, req.nbits, summary, trace, all_mode=False)
                else:
                    write_vcd_sar(out_vcd, req.nbits, summary, trace, all_mode=False)

            if out_vcd_all:
                if req.adc_type == "counter":
                    last_time_ns = write_vcd_counter(out_vcd_all, req.nbits, summary, trace, all_mode=(i>0), start_time_ns=last_time_ns+10)
                else:
                    last_time_ns = write_vcd_sar(out_vcd_all, req.nbits, summary, trace, all_mode=(i>0), start_time_ns=last_time_ns+10)

        wrote_csv = None
        if out_csv:
            write_results_csv(out_csv, [s.data for s in results])
            print(f"Wrote results CSV to {out_csv}")
            wrote_csv = out_csv
        if out_vcd:
            print(f"Wrote VCD to {out_vcd}")
        if out_vcd_all:
            print(f"Wrote VCD (all) to {out_vcd_all}")

        return RunResult(results=results, wrote_csv=wrote_csv, wrote_vcd=out_vcd, wrote_vcd_all=out_vcd_all)
