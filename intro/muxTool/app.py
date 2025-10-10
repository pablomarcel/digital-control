
from __future__ import annotations
from typing import List, Dict, Iterator
from .apis import RunRequest, RunResult
from .utils import resolve_input_path, resolve_output_path
from .io import load_rows_from_csv, load_rows_from_json, write_results_csv
from .design import write_vcd
from .core import MuxCore

class MuxApp:
    """High-level application orchestrator for muxTool."""
    def __init__(self) -> None:
        pass

    def _rows_from_request(self, req: RunRequest) -> List[Dict[str,int]]:
        csv_path = resolve_input_path(req.csv, req.in_dir) if req.csv else None
        json_spec = resolve_input_path(req.json, req.in_dir) if req.json else None
        if not (csv_path or json_spec):
            raise ValueError("Provide csv or json in RunRequest")
        if csv_path:
            it = load_rows_from_csv(csv_path)
        else:
            it = load_rows_from_json(json_spec)  # type: ignore[arg-type]
        return list(it)

    def run(self, req: RunRequest) -> RunResult:
        rows = self._rows_from_request(req)
        core = MuxCore(req.bits)
        out_rows = core.simulate(rows)

        out_csv = resolve_output_path(req.out, req.out_dir) if req.out else None
        out_vcd = resolve_output_path(req.trace, req.out_dir) if req.trace else None

        if out_csv:
            write_results_csv(out_csv, out_rows)
        if out_vcd:
            write_vcd(out_vcd, out_rows, req.bits)

        return RunResult(rows=out_rows, out_csv=out_csv, out_vcd=out_vcd)
