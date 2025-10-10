from __future__ import annotations
from typing import List, Dict, Any
from .apis import RunRequest, RunResult, Row, Update
from .core import WeightedDAC, R2RDAC
from .io import load_vectors_from_csv, load_vectors_from_json
from .design import write_results_csv, write_vcd
from .utils import resolve_input_path, resolve_output_path, timecall

def _fmt_rows_for_csv(meta_common: Dict[str, Any], entries: List[Dict[str, Any]]):
    rows = []
    for r in entries:
        m = dict(meta_common)
        m.update(r)
        rows.append(m)
    return rows

@timecall
def run(req: RunRequest) -> RunResult:
    # Resolve paths
    csv_path  = resolve_input_path(req.csv,  req.in_dir)  if req.csv  else None
    json_spec = resolve_input_path(req.jspec, req.in_dir) if req.jspec else None
    out_csv   = resolve_output_path(req.out_csv, req.out_dir) if req.out_csv else None
    out_vcd   = resolve_output_path(req.out_vcd, req.out_dir) if req.out_vcd else None
    out_vcd_all = resolve_output_path(req.out_vcd_all, req.out_dir) if req.out_vcd_all else None

    # Load vectors
    if csv_path:
        vecs = list(load_vectors_from_csv(csv_path, req.nbits))
    elif json_spec:
        vecs = list(load_vectors_from_json(json_spec, req.nbits))
    else:
        raise ValueError("Provide csv or jspec (JSON) for input vectors.")
    if not vecs:
        return RunResult(rows=[], updates=[], messages=["No input vectors."])

    # Pick engine
    dtype = req.dac_type.lower().strip()
    if dtype == "weighted":
        engine = WeightedDAC(
            nbits=req.nbits, vref=req.vref, ro_over_r=req.ro_over_r,
            gain_err=req.gain_err, vo_offset=req.vo_offset,
            res_sigma_pct=req.res_sigma_pct
        )
        meta = dict(nbits=req.nbits, vref=req.vref, ro_over_r=req.ro_over_r,
                    gain_err=req.gain_err, vo_offset=req.vo_offset,
                    res_sigma_pct=req.res_sigma_pct)
    elif dtype == "r2r":
        engine = R2RDAC(
            nbits=req.nbits, vref=req.vref, R_ohm=req.R_ohm,
            sigma_r_pct=req.sigma_r_pct, sigma_2r_pct=req.sigma_2r_pct,
            gain_err=req.gain_err, vo_offset=req.vo_offset
        )
        meta = dict(nbits=req.nbits, vref=req.vref, R_ohm=req.R_ohm,
                    sigma_r_pct=req.sigma_r_pct, sigma_2r_pct=req.sigma_2r_pct,
                    gain_err=req.gain_err, vo_offset=req.vo_offset)
    else:
        raise ValueError("dac_type must be 'r2r' or 'weighted'")

    # Run
    rows_for_csv: List[Dict[str, Any]] = []
    updates: List[Update] = []
    for i, v in enumerate(vecs):
        code = int(v['code'])
        bits = v['bits']
        vo_id  = engine.vo_ideal_bits(bits)
        vo_non = engine.vo_nonideal_bits(bits)
        rows_for_csv.append({
            **meta,
            'code': code,
            'vo_ideal': vo_id,
            'vo_nonideal': vo_non,
            'error': vo_non - vo_id,
        })
        updates.append(Update(code=code, vo_ideal=vo_id, vo_nonideal=vo_non))

    # Persist
    msgs = []
    if out_csv:
        write_results_csv(out_csv, rows_for_csv)
        msgs.append(f"Wrote results CSV to {out_csv}")
    if out_vcd:
        write_vcd(out_vcd, req.nbits, updates, tupd=req.tupd,
                  start_time_ns=0, all_mode=False, include_ideal=req.include_ideal_in_vcd)
        msgs.append(f"Wrote VCD to {out_vcd}")
    if out_vcd_all:
        write_vcd(out_vcd_all, req.nbits, updates, tupd=req.tupd,
                  start_time_ns=0, all_mode=False, include_ideal=req.include_ideal_in_vcd)
        msgs.append(f"Wrote VCD (all) to {out_vcd_all}")

    return RunResult(rows=[Row(meta=r) for r in rows_for_csv], updates=updates, messages=msgs)
