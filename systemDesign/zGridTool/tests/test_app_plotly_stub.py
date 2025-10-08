
# -*- coding: utf-8 -*-
from __future__ import annotations
from types import SimpleNamespace
from pathlib import Path
import builtins

import systemDesign.zGridTool.app as app_mod
from systemDesign.zGridTool.apis import RunRequest
from systemDesign.zGridTool.app import ZGridApp

class _FakeFig:
    def write_html(self, path, include_plotlyjs=None, full_html=True, config=None):
        p = Path(path); p.parent.mkdir(parents=True, exist_ok=True); p.write_text("<html></html>")
    def write_image(self, path, width=None, height=None, scale=None):
        p = Path(path); p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b"PNG")

def _fake_draw_plotly(**kwargs):
    return _FakeFig()

def test_app_plotly_branch(monkeypatch, tmp_path):
    # Patch the draw_plotly used by app so we don't need plotly/kaleido installed
    monkeypatch.setattr(app_mod, "draw_plotly", lambda **kw: _fake_draw_plotly(**kw))
    req = RunRequest(T=0.05, backend="plotly", plotly_html="stub.html", png="stub.png", verbose=False)
    zapp = ZGridApp()
    out = zapp.run(req)
    assert out.html_path and out.html_path.endswith("stub.html")
    # PNG may or may not be written depending on the fake, but in our stub we do write it
    assert out.png_path and out.png_path.endswith("stub.png")
