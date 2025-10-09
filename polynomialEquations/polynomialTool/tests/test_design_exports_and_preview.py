
import os, numpy as np, json
from polynomialEquations.polynomialTool.design import polydesign, rst_design, model_match

def test_polydesign_exports(tmp_path):
    res = polydesign(A=[1,-2,1], B=[0.02,0.02], H=[1,-1.2,0.52], F=[1,0],
                     layout='ogata', config=2, backend='none', kmax=5, T=1.0,
                     export_json=str(tmp_path/'pd.json'),
                     export_csv=str(tmp_path/'pd.csv'))
    assert 'alpha' in res and os.path.exists(tmp_path/'pd.json') and os.path.exists(tmp_path/'pd.csv')

def test_rst_design_no_save(tmp_path):
    res = rst_design(A=[1,-2,1], B=[0.02,0.02], H=[1,-1.2,0.52], F=[1,0],
                     layout='ogata', config=2, backend='none', kmax=5, T=1.0)
    assert 'num' in res and 'den' in res

def test_model_match_backend_none(tmp_path):
    res = model_match(A=[1,-1.3679,0.3679], B=[0.3679,0.2642],
                      Gnum=[0.62,-0.3], Gden=[1,-1.2,0.52],
                      H1=[1,0.5], F=[1,0], layout='ogata',
                      backend='none', kmax=5, T=1.0,
                      export_json=str(tmp_path/'mm.json'))
    assert 'alpha' in res and os.path.exists(tmp_path/'mm.json')
