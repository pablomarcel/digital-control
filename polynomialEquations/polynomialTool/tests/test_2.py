from polynomialEquations.polynomialTool.apis import RunRequest
from polynomialEquations.polynomialTool.app import PolynomialApp
def test_app_polydesign_smoke():
    app = PolynomialApp()
    req = RunRequest(mode='polydesign', A=[1,-2,1], B=[0.02,0.02], H=[1,-1.2,0.52], F=[1,0], layout='ogata', config=2, backend='none')
    res = app.run(req)
    assert 'alpha' in res and 'beta' in res
