
from __future__ import annotations
from rstControllers.rstPlotTool.apis import RunRequest, YLimits, OverlayFilters

def test_dataclasses_defaults_and_custom():
    req = RunRequest(files=['a.csv'])
    assert req.backend in ('both','mpl','plotly')
    assert req.ylimits.ylimY is None
    # Custom
    yl = YLimits(ylimY=(0.0,1.0), ylimU=(-1,1), ylimE=(-0.5,0.5))
    flt = OverlayFilters(include='*.csv', exclude='bad_*')
    req2 = RunRequest(files=['b.csv'], overlay=True, backend='mpl', style='dark',
                      dpi=200, kmin=0, kmax=100, robust=1.0, ylimits=yl,
                      clip=True, legend='full', filters=flt, annotate='x.json',
                      title='Hello')
    assert req2.overlay is True
    assert req2.ylimits.ylimU == (-1,1)
    assert req2.filters.include == '*.csv'
