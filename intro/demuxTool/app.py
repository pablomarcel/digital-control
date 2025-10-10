from __future__ import annotations
from typing import List, Dict
from .apis import RunRequest, RunResult
from .utils import resolve_input_path, resolve_output_path
from .io import load_rows_from_csv, load_rows_from_json, write_results_csv, write_vcd
from .core import DemuxCircuit

class DemuxApp:
    """High-level orchestration: parse inputs, run circuit, write outputs."""
    def run(self, req: RunRequest) -> RunResult:
        # Resolve paths
        csv_path  = resolve_input_path(req.csv_path,  req.in_dir)  if req.csv_path  else None
        json_spec = resolve_input_path(req.json_spec, req.in_dir)  if req.json_spec else None
        out_csv   = resolve_output_path(req.out_csv,   req.out_dir) if req.out_csv   else None
        out_vcd   = resolve_output_path(req.out_vcd,   req.out_dir) if req.out_vcd   else None

        if not csv_path and not json_spec:
            raise ValueError("Provide csv_path or json_spec in RunRequest")

        # Load vectors
        if csv_path:
            vectors = list(load_rows_from_csv(csv_path))
        else:
            vectors = list(load_rows_from_json(json_spec))  # type: ignore[arg-type]

        # Build & simulate
        circuit = DemuxCircuit(req.n_outputs, req.data_bw, req.strict)
        rows = circuit.simulate(vectors)

        # Optional outputs
        if out_csv:
            write_results_csv(out_csv, rows, req.n_outputs)
        if out_vcd:
            write_vcd(out_vcd, rows, req.data_bw, req.n_outputs, circuit.sel_bits)

        return RunResult(rows=rows,
                         sel_bits=circuit.sel_bits,
                         data_bw=req.data_bw,
                         n_outputs=req.n_outputs,
                         out_csv=out_csv,
                         out_vcd=out_vcd)
