
from __future__ import annotations
from rst_controllers.rstTool.app import RSTApp
from rst_controllers.rstTool.apis import RunRequest

def test_smoke_unity_dc():
    app=RSTApp()
    req=RunRequest(A=[1.0,-0.8],B=[0.5],d=1,poles=[0.6,0.6],Tmode="unity_dc",N=40,export_json="unity.json",save_csv="unity.csv")
    res=app.run(req)
    assert res.csv_path and res.json_path
    assert 0.0 <= res.y_final <= 1.2

def test_integrator_unity():
    app=RSTApp()
    req=RunRequest(A=[1.0,-0.8],B=[0.5],d=1,poles=[0.6,0.6,0.3],integrator=True,Tmode="unity_dc",N=60)
    res=app.run(req)
    assert abs(res.y_final-1.0) < 0.25
