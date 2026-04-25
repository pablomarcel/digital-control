from __future__ import annotations

from typing import Any, Dict, List, Optional

from .utils import log_call, mask


class MuxCore:
    """Core 4:1 mux simulator.

    The runtime implementation prefers PyRTL when it is available, but the module
    remains importable without PyRTL so Sphinx autodoc and lightweight CI jobs do
    not fail just because optional simulation dependencies are missing.

    The logical behavior is always::

        y = d0  when sel == 0
        y = d1  when sel == 1
        y = d2  when sel == 2
        y = d3  when sel == 3

    Parameters
    ----------
    data_bw:
        Data-path bit width used to mask ``d0`` through ``d3`` and ``y``.
    prefer_pyrtl:
        If true, use PyRTL when it is installed. If false, always use the pure
        Python fallback simulator.
    """

    def __init__(self, data_bw: int = 8, *, prefer_pyrtl: bool = True) -> None:
        self.data_bw = int(data_bw)
        if self.data_bw <= 0:
            raise ValueError("data_bw must be a positive integer")
        self.prefer_pyrtl = bool(prefer_pyrtl)
        self.ports: Dict[str, Any] = {}
        self._rtl: Optional[Any] = None

    @staticmethod
    def _import_pyrtl() -> Any:
        """Import PyRTL lazily.

        Keeping this import inside a method prevents Sphinx autodoc from failing
        when PyRTL is not installed in the documentation environment.
        """
        try:
            import pyrtl as rtl  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover - depends on environment
            raise RuntimeError(
                "PyRTL is required for hardware-backed mux simulation. "
                "Install pyrtl or run with the pure-Python fallback."
            ) from exc
        return rtl

    def _normalized_inputs(self, row: Dict[str, int]) -> Dict[str, int]:
        """Return one input row masked to the configured bit widths."""
        missing = [name for name in ("sel", "d0", "d1", "d2", "d3") if name not in row]
        if missing:
            raise KeyError(f"Missing mux input field(s): {', '.join(missing)}")
        return {
            "sel": mask(row["sel"], 2),
            "d0": mask(row["d0"], self.data_bw),
            "d1": mask(row["d1"], self.data_bw),
            "d2": mask(row["d2"], self.data_bw),
            "d3": mask(row["d3"], self.data_bw),
        }

    @staticmethod
    def _mux_value(row: Dict[str, int]) -> int:
        """Return the selected data input for one normalized row."""
        return int(row[f"d{int(row['sel'])}"])

    @log_call
    def build(self) -> Dict[str, Any]:
        """Build the PyRTL mux circuit and return its ports.

        This method is only needed when PyRTL-backed simulation is desired. It
        intentionally imports PyRTL lazily so importing this module stays safe
        for documentation builds.
        """
        rtl = self._import_pyrtl()
        rtl.reset_working_block()

        sel = rtl.Input(2, "sel")
        d0 = rtl.Input(self.data_bw, "d0")
        d1 = rtl.Input(self.data_bw, "d1")
        d2 = rtl.Input(self.data_bw, "d2")
        d3 = rtl.Input(self.data_bw, "d3")
        y = rtl.Output(self.data_bw, "y")
        y <<= rtl.mux(sel, d0, d1, d2, d3)

        self._rtl = rtl
        self.ports = {"sel": sel, "d0": d0, "d1": d1, "d2": d2, "d3": d3, "y": y}
        return self.ports

    @log_call
    def simulate_python(self, vectors: List[Dict[str, int]]) -> List[Dict[str, int]]:
        """Simulate the mux with a dependency-free Python implementation."""
        out_rows: List[Dict[str, int]] = []
        for i, row in enumerate(vectors):
            provided = self._normalized_inputs(row)
            out_rows.append({"cycle": i, **provided, "y": self._mux_value(provided)})
        return out_rows

    @log_call
    def simulate_pyrtl(self, vectors: List[Dict[str, int]]) -> List[Dict[str, int]]:
        """Simulate the mux with PyRTL."""
        if not self.ports:
            self.build()
        rtl = self._rtl if self._rtl is not None else self._import_pyrtl()
        sim = rtl.Simulation()

        out_rows: List[Dict[str, int]] = []
        for i, row in enumerate(vectors):
            provided = self._normalized_inputs(row)
            sim.step(provided_inputs=provided)
            y = sim.inspect("y")
            out_rows.append({"cycle": i, **provided, "y": int(y)})
        return out_rows

    @log_call
    def simulate(self, vectors: List[Dict[str, int]]) -> List[Dict[str, int]]:
        """Simulate the mux, using PyRTL when available and Python otherwise."""
        if self.prefer_pyrtl:
            try:
                return self.simulate_pyrtl(vectors)
            except RuntimeError:
                return self.simulate_python(vectors)
        return self.simulate_python(vectors)
