from __future__ import annotations
import os, sys
from intro.demuxTool import design
from intro.demuxTool.tools import class_diagram as cd_mod

def test_class_diagram_dot_string(tmp_path):
    # No Graphviz or dot: validate we can obtain DOT text and persist it ourselves
    dot = design.class_diagram_dot()
    assert "digraph" in dot and "DemuxTool" in dot
    out = tmp_path / "diagram.dot"
    out.write_text(dot, encoding="utf-8")
    assert out.exists() and out.stat().st_size > 0

def test_tools_class_diagram_main_stubbed(tmp_path, monkeypatch):
    # Stub out the render function used by the tool to avoid Graphviz entirely
    def fake_render(out_path: str) -> str:
        # Write a minimal DOT file and return its path
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("digraph G {A->B}")
        return out_path

    monkeypatch.setattr(cd_mod, "render_class_diagram", fake_render, raising=True)

    outstem = tmp_path / "demo_diagram"
    old = sys.argv
    try:
        sys.argv = [old[0], "--out", str(outstem)]
        cd_mod.main()
    finally:
        sys.argv = old

    # The stub writes a raw DOT at the exact path; ensure it exists
    assert os.path.exists(str(outstem))
    assert os.path.isfile(str(outstem))
    assert os.path.getsize(str(outstem)) > 0
