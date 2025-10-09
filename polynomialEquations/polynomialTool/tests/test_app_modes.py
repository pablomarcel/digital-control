
import json, os, numpy as np
from polynomialEquations.polynomialTool.apis import RunRequest
from polynomialEquations.polynomialTool.app import PolynomialApp

def test_app_solve_mode(tmp_path):
    app = PolynomialApp()
    req = RunRequest(mode='solve', A=[1,1,0.5], B=[1,2], D=[1,0,0,0], layout='ogata')
    res = app.run(req)
    assert np.allclose(res['alpha'], [1.0,-1.2], atol=1e-6)
    assert np.allclose(res['beta'], [0.2,0.3], atol=1e-6)

def test_app_rst_mode_with_parity(tmp_path):
    app = PolynomialApp()
    # F has trailing zero -> parity should increase delay internally without crashing
    req = RunRequest(mode='rst', A=[1,-2,1], B=[0.02,0.02], H=[1,-1.2,0.52], F=[1,0], ogata_parity=True,
                     layout='ogata', rst_config=2, backend='none', save=None, T=1.0, kmax=5,
                     export_json=str(tmp_path/'rst.json'))
    res = app.run(req)
    assert 'alpha' in res and 'beta' in res
    assert os.path.exists(tmp_path/'rst.json')

def test_app_modelmatch_mode(tmp_path):
    app = PolynomialApp()
    req = RunRequest(mode='modelmatch',
                     A=[1,-1.3679,0.3679], B=[0.3679,0.2642],
                     Gmodel_num=[0.62,-0.3], Gmodel_den=[1,-1.2,0.52],
                     H1=[1,0.5], F=[1,0], layout='ogata',
                     backend='none', kmax=5, T=1.0,
                     export_json=str(tmp_path/'mm.json'))
    res = app.run(req)
    assert 'alpha' in res and 'beta' in res
    assert os.path.exists(tmp_path/'mm.json')
