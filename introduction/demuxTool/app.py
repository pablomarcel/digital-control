#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Application orchestration for :mod:`introduction.demuxTool`."""
from __future__ import annotations

from typing import Dict, List

try:  # Package imports
    from .apis import RunRequest, RunResult
    from .io import load_rows_from_csv, load_rows_from_json, write_results_csv, write_vcd
    from .utils import resolve_input_path, resolve_output_path
except ImportError:  # pragma: no cover - direct script/import fallback
    from apis import RunRequest, RunResult  # type: ignore
    from io import load_rows_from_csv, load_rows_from_json, write_results_csv, write_vcd  # type: ignore
    from utils import resolve_input_path, resolve_output_path  # type: ignore


class DemuxApp:
    """High-level demultiplexer workflow.

    The app resolves input/output paths, loads CSV or JSON vectors, runs the
    demultiplexer circuit, and writes optional CSV/VCD outputs.
    """

    def _load_vectors(self, req: RunRequest) -> List[Dict[str, int]]:
        """Resolve and load vectors from the selected input source."""
        csv_path = resolve_input_path(req.csv_path, req.in_dir) if req.csv_path else None
        json_spec = resolve_input_path(req.json_spec, req.in_dir) if req.json_spec else None

        if not csv_path and not json_spec:
            raise ValueError("Provide csv_path or json_spec in RunRequest")

        if csv_path:
            return list(load_rows_from_csv(csv_path))
        return list(load_rows_from_json(json_spec))  # type: ignore[arg-type]

    def run(self, req: RunRequest) -> RunResult:
        """Run a complete demux simulation."""
        # Lazy import keeps this module safe for Sphinx autodoc when optional
        # runtime dependencies are not installed.
        try:
            from .core import DemuxCircuit
        except ImportError:  # pragma: no cover - direct script/import fallback
            from core import DemuxCircuit  # type: ignore

        vectors = self._load_vectors(req)
        out_csv = resolve_output_path(req.out_csv, req.out_dir) if req.out_csv else None
        out_vcd = resolve_output_path(req.out_vcd, req.out_dir) if req.out_vcd else None

        circuit = DemuxCircuit(req.n_outputs, req.data_bw, req.strict)
        rows = circuit.simulate(vectors)

        if out_csv:
            write_results_csv(out_csv, rows, req.n_outputs)
        if out_vcd:
            write_vcd(out_vcd, rows, req.data_bw, req.n_outputs, circuit.sel_bits)

        return RunResult(
            rows=rows,
            sel_bits=circuit.sel_bits,
            data_bw=req.data_bw,
            n_outputs=req.n_outputs,
            out_csv=out_csv,
            out_vcd=out_vcd,
        )
