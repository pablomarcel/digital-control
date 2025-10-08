
import numpy as np
import types
from zPlaneAnalysis.discreteResponseTool.apis import RunRequest
from zPlaneAnalysis.discreteResponseTool.app import DiscreteResponseApp
from zPlaneAnalysis.discreteResponseTool import design

class DummyAx:
    def __init__(self): pass
    def set_aspect(self,*a,**k): pass
    def set_xlim(self,*a,**k): pass
    def set_ylim(self,*a,**k): pass
    def axhline(self,*a,**k): pass
    def axvline(self,*a,**k): pass
    def plot(self,*a,**k): pass
    def set_title(self,*a,**k): pass
    def set_xlabel(self,*a,**k): pass
    def set_ylabel(self,*a,**k): pass
    def legend(self,*a,**k): pass
    def add_patch(self,*a,**k): pass
    def grid(self,*a,**k): pass

class DummyFig:
    def __init__(self): pass
    def add_gridspec(self, *a, **k): return ((0,0),(0,1),(0,2))
    def add_subplot(self, *a, **k): return DummyAx()
    def savefig(self, *a, **k): pass

class DummyPLT(types.SimpleNamespace):
    def subplots(self, *a, **k): return DummyFig(), DummyAx()
    def close(self, *a, **k): pass
    def figure(self, *a, **k): return DummyFig()

class DummyGO:
    class Figure:
        def __init__(self): pass
        def add_trace(self, *a, **k): pass
        def update_layout(self, *a, **k): pass
        def write_html(self, path): open(path,"w").write("<html></html>")
    class Scatter:
        def __init__(self, *a, **k): pass

def test_app_run_all_exports(tmp_path, monkeypatch):
    # Monkeypatch plotting backends used inside app via design module
    monkeypatch.setattr(design, "plt", DummyPLT())
    class C: 
        def __init__(self, *a, **k): pass
    monkeypatch.setattr(design, "Circle", C)
    monkeypatch.setattr(design, "go", DummyGO())

    req = RunRequest(
        example37=True, N=10,
        matplotlib=str(tmp_path / "resp.png"),
        pzmap=str(tmp_path / "pz.png"),
        rlocus=str(tmp_path / "rl.png"),
        plotly_step=str(tmp_path / "step.html"),
        plotly_pz=str(tmp_path / "pz.html"),
        plotly_rl=str(tmp_path / "rl.html"),
        panel=str(tmp_path / "panel.png"),
        outdir=str(tmp_path)
    )
    app = DiscreteResponseApp(req)
    out = app.run(
        matplotlib=req.matplotlib, csv=None, pzmap=req.pzmap, rlocus=req.rlocus,
        plotly_step=req.plotly_step, plotly_pz=req.plotly_pz, plotly_rl=req.plotly_rl,
        panel=req.panel, outdir=req.outdir
    )
    # Confirm keys present and arrays reasonable
    assert "metrics" in out and "k" in out and "y" in out
    assert len(out["k"]) == 10 and len(out["y"]) == 10
