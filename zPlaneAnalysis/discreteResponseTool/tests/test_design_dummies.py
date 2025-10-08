
import types
import numpy as np
from zPlaneAnalysis.discreteResponseTool import design

class DummyAx:
    def __init__(self): self.calls=[]
    def set_aspect(self,*a,**k): pass
    def set_xlim(self,*a,**k): pass
    def set_ylim(self,*a,**k): pass
    def axhline(self,*a,**k): pass
    def axvline(self,*a,**k): pass
    def plot(self,*a,**k): self.calls.append(("plot", a, k))
    def set_title(self,*a,**k): pass
    def set_xlabel(self,*a,**k): pass
    def set_ylabel(self,*a,**k): pass
    def legend(self,*a,**k): pass
    def add_patch(self,*a,**k): pass
    def grid(self,*a,**k): pass

class DummyGridSpec:
    def __getitem__(self, idx):
        # return something acceptable to fig.add_subplot(...)
        return (0,0)

class DummyFig:
    def __init__(self): pass
    def add_gridspec(self, *a, **k):
        return DummyGridSpec()
    def add_subplot(self, *a, **k): return DummyAx()
    def savefig(self, *a, **k): pass

class DummyPLT(types.SimpleNamespace):
    def subplots(self, *a, **k): return DummyFig(), DummyAx()
    def close(self, *a, **k): pass
    def figure(self, *a, **k): return DummyFig()

class DummyGO:
    class Figure:
        def __init__(self): self.traces=[]
        def add_trace(self, *a, **k): self.traces.append((a,k))
        def update_layout(self, *a, **k): pass
        def write_html(self, path): open(path,"w").write("<html></html>")
    class Scatter:
        def __init__(self, *a, **k): pass

def test_design_functions_execute(tmp_path, monkeypatch):
    # Monkeypatch plotting backends
    monkeypatch.setattr(design, "plt", DummyPLT())
    class C: 
        def __init__(self, *a, **k): pass
    monkeypatch.setattr(design, "Circle", C)
    monkeypatch.setattr(design, "go", DummyGO())

    # Small system (stable)
    num = np.array([0.1])
    den = np.array([1.0, -0.8])

    # Matplotlib exports
    pz = tmp_path / "pz.png"
    rl = tmp_path / "rl.png"
    panel = tmp_path / "panel.png"
    design.pzmap(num, den, path=str(pz), clip=1.5)
    design.root_locus(num, den, Kmin=0, Kmax=1, NK=10, rclip=1.5, path=str(rl))
    design.panel_plot(np.arange(5), np.linspace(0,1,5), num, den, num, den, path=str(panel))

    # Plotly exports
    step_html = tmp_path / "s.html"
    pz_html = tmp_path / "p.html"
    rl_html = tmp_path / "r.html"
    design.plotly_step(list(range(5)), [0,1,2,1,0], str(step_html))
    design.plotly_pz(num, den, str(pz_html))
    design.plotly_rlocus(num, den, str(rl_html), Kmin=0.0, Kmax=1.0, NK=10)

    # Files should be created
    assert step_html.exists() and pz_html.exists() and rl_html.exists()
