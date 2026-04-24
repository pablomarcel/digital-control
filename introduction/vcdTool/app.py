from __future__ import annotations
from typing import List
import os

from .apis import RunRequest
from .core import VCDParser, WaveformBuilder, Decoder
from .io import resolve_input_path, resolve_output_path, export_csv
from .design import plot_mpl, plot_plotly

class VCDApp:
    """Top-level orchestration for VCD plotting pipeline."""
    def __init__(self) -> None:
        self.parser = VCDParser()
        self.builder = WaveformBuilder()
        self.decoder = Decoder()

    def run(self, req: RunRequest) -> dict:
        req.validate()
        vcd_path  = resolve_input_path(req.vcd, req.in_dir)
        png_path  = resolve_output_path(req.png, req.out_dir)
        html_path = resolve_output_path(req.html, req.out_dir)
        csv_path  = resolve_output_path(req.out_csv, req.out_dir)

        vcd = self.parser.parse(vcd_path)
        if not vcd.events:
            raise RuntimeError("No waveform events found in VCD.")

        all_names = [v.name for v in vcd.vars_by_id.values()]
        wanted = req.signals if req.signals else all_names[:8]

        times_ticks, series, rawbits, widths = self.builder.build(vcd, wanted)
        times_sec = [t * vcd.timescale_factor for t in times_ticks]

        if req.decode:
            self.decoder.apply(series, rawbits, widths, req.decode)

        title = os.path.basename(vcd_path) + f"  (units: {req.units})"
        if csv_path: export_csv(csv_path, times_sec, series, req.csv_units)
        if req.backend == 'mpl':
            plot_mpl(png_path, times_sec, series, widths, req.units, title)
        else:
            plot_plotly(html_path, times_sec, series, widths, req.units, title, overlay=req.overlay)

        return {
            "vcd": vcd_path,
            "signals": list(series.keys()),
            "out": {"png": png_path, "html": html_path, "csv": csv_path}
        }
