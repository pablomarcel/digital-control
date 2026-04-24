from __future__ import annotations
import types
from pathlib import Path
from pole_placement.poleTool.utils import to_real_if_close, mat_to_str, ensure_out_dir, timeit

def test_utils_misc(tmp_path):
    M = to_real_if_close([[1+1e-14j, 2],[3,4]])
    s = mat_to_str(M)
    assert "1.000000" in s and "2.000000" in s
    out = ensure_out_dir(override=str(tmp_path))
    assert out.exists()
    @timeit
    def f(x): return x+1
    assert f(2)==3  # wrapper works

def test_class_diagram(tmp_path, monkeypatch):
    # Write PUML in a temp out dir
    from pole_placement.poleTool.tools import class_diagram
    class_diagram.main(out=str(tmp_path))
    p = Path(__file__).resolve().parents[2] / "out" / "poleTool_class_diagram.puml"
    # The tool writes to package/OUT; we also asked it to use tmp_path via 'out' arg
    # Accept either location depending on import path; at least one should exist.
    assert p.exists() or (tmp_path/"poleTool_class_diagram.puml").exists()
