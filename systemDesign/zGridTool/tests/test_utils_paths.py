
# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
from systemDesign.zGridTool.utils import ensure_in_path, ensure_out_path

def test_utils_paths(tmp_path, monkeypatch):
    # Force OUT_DIR/IN_DIR to our tmp_path by monkeypatching module-level constants
    import systemDesign.zGridTool.utils as U
    monkeypatch.setattr(U, "IN_DIR", tmp_path / "in", raising=False)
    monkeypatch.setattr(U, "OUT_DIR", tmp_path / "out", raising=False)

    p_in_rel = ensure_in_path("foo.txt")
    p_out_rel = ensure_out_path("bar.txt")
    assert str(p_in_rel).endswith("in/foo.txt")
    assert str(p_out_rel).endswith("out/bar.txt")

    p_out_abs = ensure_out_path(str(tmp_path / "abs.png"))
    assert p_out_abs == tmp_path / "abs.png"
