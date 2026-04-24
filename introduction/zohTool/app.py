from __future__ import annotations
from typing import List
from .apis import RunRequest, RunResult
from .core import ZOHModel, ZOHSimulator
from .io import load_u_from_csv, load_u_from_json
from .design import CSVExporter, VCDWriter
from .utils import resolve_input_path, resolve_output_path

class ZOHApp:
    """Thin orchestrator to run ZOH end-to-end in a testable way."""
    def run(self, req: RunRequest) -> RunResult:
        msgs: List[str] = []

        # Resolve paths
        csv_path  = resolve_input_path(req.csv,      req.in_dir) if req.csv      else None
        json_spec = resolve_input_path(req.json_spec, req.in_dir) if req.json_spec else None
        out_csv   = resolve_output_path(req.out_csv, req.out_dir) if req.out_csv else None
        out_vcd   = resolve_output_path(req.out_vcd, req.out_dir) if req.out_vcd else None

        # Load input sequence
        if csv_path:
            u = load_u_from_csv(csv_path)
            msgs.append(f"Loaded {len(u)} samples from CSV: {csv_path}")
        else:
            if not json_spec:
                raise ValueError("Either csv or json_spec must be provided.")
            u = load_u_from_json(json_spec)
            msgs.append(f"Loaded {len(u)} samples from JSON spec.")

        if not u:
            msgs.append("No samples to process.")
            return RunResult(messages=msgs)

        # Build events
        model = ZOHModel(Ts=req.Ts, delay=req.delay, droop_tau=req.droop_tau, offset=req.offset)
        sim = ZOHSimulator(model)
        events = sim.expand(u)

        # Exports
        wrote_csv = None
        if out_csv:
            CSVExporter().write_results_csv(out_csv, events, units=req.units)
            wrote_csv = out_csv
            msgs.append(f"Wrote results CSV to {out_csv}")

        wrote_vcd = None
        if out_vcd:
            VCDWriter().write_vcd_zoh(out_vcd, events, scale=req.scale, idx_bits=req.idx_bits)
            wrote_vcd = out_vcd
            msgs.append(f"Wrote VCD to {out_vcd}")

        return RunResult(events=events, messages=msgs, wrote_csv=wrote_csv, wrote_vcd=wrote_vcd)
