#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Core demultiplexer model for :mod:`introduction.demuxTool`.

The production simulator prefers PyRTL when it is installed, but this module is
safe to import in documentation environments that do not install optional EDA
packages.  A small pure-Python simulator is kept as a deterministic fallback so
Sphinx autodoc and lightweight CI jobs can import the package without pulling in
``pyrtl``.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List

try:  # Package import
    from .utils import mask
except ImportError:  # pragma: no cover - direct script/import fallback
    from utils import mask  # type: ignore


class DemuxCircuit:
    """Combinational N-way demultiplexer.

    The demultiplexer routes one data word ``x`` to exactly one output ``yN``
    according to the select value ``sel``. All non-selected outputs are zero.

    Parameters
    ----------
    n_outputs:
        Number of demultiplexer outputs. Must be at least 2.
    data_bw:
        Data bit width for the input and each output.
    strict:
        When ``True``, selections outside ``0 <= sel < n_outputs`` drive all
        outputs to zero. When ``False``, the select word is simply masked to the
        internal select width, matching the original PyRTL-oriented behavior.

    Notes
    -----
    ``build()`` requires the optional :mod:`pyrtl` package. ``simulate()`` uses
    PyRTL when available and otherwise falls back to a pure-Python equivalent.
    This keeps the package importable during Sphinx builds where PyRTL may not
    be installed.
    """

    def __init__(self, n_outputs: int = 4, data_bw: int = 8, strict: bool = False):
        if int(n_outputs) < 2:
            raise ValueError("n_outputs must be >= 2")
        if int(data_bw) < 1:
            raise ValueError("data_bw must be >= 1")

        self.n_outputs = int(n_outputs)
        self.data_bw = int(data_bw)
        self.strict = bool(strict)
        self.sel_bits = max(1, int(math.ceil(math.log2(self.n_outputs))))
        self.ports: Dict[str, Any] | None = None

    @staticmethod
    def _import_pyrtl():
        """Import PyRTL lazily and return the module.

        Lazy import is intentional: documentation jobs can import this module
        without having PyRTL installed. Runtime users still get a clear error if
        they explicitly request a PyRTL circuit build without the dependency.
        """
        try:
            import pyrtl as rtl  # type: ignore
        except ModuleNotFoundError as exc:  # pragma: no cover - environment-specific
            raise RuntimeError(
                "PyRTL is required for DemuxCircuit.build(). Install pyrtl or "
                "use DemuxCircuit.simulate(), which has a pure-Python fallback."
            ) from exc
        return rtl

    def build(self) -> Dict[str, Any]:
        """Build the PyRTL combinational demultiplexer and return its ports.

        Returns
        -------
        dict
            Mapping with ``sel``, ``x``, and ``ys`` PyRTL wire objects.
        """
        rtl = self._import_pyrtl()
        rtl.reset_working_block()

        sel = rtl.Input(self.sel_bits, "sel")
        x = rtl.Input(self.data_bw, "x")

        max_code = rtl.Const(self.n_outputs - 1, bitwidth=self.sel_bits)
        valid = sel <= max_code
        zero = rtl.Const(0, bitwidth=self.data_bw)
        ys = []

        for i in range(self.n_outputs):
            y = rtl.Output(self.data_bw, f"y{i}")
            eq = sel == rtl.Const(i, bitwidth=self.sel_bits)
            pred = (eq & valid) if self.strict else eq
            y <<= rtl.select(pred, x, zero)
            ys.append(y)

        self.ports = {"sel": sel, "x": x, "ys": ys}
        return self.ports

    def _simulate_python(self, vectors: List[Dict[str, int]]) -> List[Dict[str, int]]:
        """Simulate the demultiplexer with pure Python logic."""
        out_rows: List[Dict[str, int]] = []
        for i, row in enumerate(vectors):
            sel_raw = int(row["sel"])
            x = mask(int(row["x"]), self.data_bw)
            sel = mask(sel_raw, self.sel_bits)

            record: Dict[str, int] = {"cycle": i, "sel": sel, "x": x}
            valid = 0 <= sel_raw < self.n_outputs if self.strict else True
            for k in range(self.n_outputs):
                record[f"y{k}"] = x if valid and sel == k else 0
            out_rows.append(record)
        return out_rows

    def _simulate_pyrtl(self, vectors: List[Dict[str, int]]) -> List[Dict[str, int]]:
        """Simulate the demultiplexer with PyRTL."""
        rtl = self._import_pyrtl()
        if self.ports is None:
            self.build()

        sim = rtl.Simulation()
        out_rows: List[Dict[str, int]] = []
        for i, row in enumerate(vectors):
            sel = mask(int(row["sel"]), self.sel_bits)
            x = mask(int(row["x"]), self.data_bw)
            sim.step(provided_inputs={"sel": sel, "x": x})

            record: Dict[str, int] = {"cycle": i, "sel": sel, "x": x}
            for k in range(self.n_outputs):
                record[f"y{k}"] = int(sim.inspect(f"y{k}"))
            out_rows.append(record)
        return out_rows

    def simulate(self, vectors: List[Dict[str, int]]) -> List[Dict[str, int]]:
        """Simulate the demultiplexer for a list of input vectors.

        The method uses PyRTL when it is importable. If PyRTL is missing, the
        pure-Python fallback returns the same row schema.
        """
        try:
            self._import_pyrtl()
        except RuntimeError:
            return self._simulate_python(vectors)
        return self._simulate_pyrtl(vectors)
