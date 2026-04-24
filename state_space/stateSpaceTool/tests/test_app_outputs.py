
import json, os, io, sys
from state_space.stateSpaceTool.app import StateSpaceApp
from state_space.stateSpaceTool.apis import RunRequest

def test_app_json_and_latex_outputs(tmp_path):
    app = StateSpaceApp()
    json_out = tmp_path / "ss.json"
    tex_out = tmp_path / "ss.tex"
    req = RunRequest(form="expr", num="z+1", den="z**2+1.3*z+0.4",
                     forms="cont,obs,diag,jordan", json_out=str(json_out),
                     latex_out=str(tex_out), check="brief")
    res = app.run(req)
    assert json_out.exists() and tex_out.exists()
    data = json.loads(json_out.read_text())
    assert "cont" in data and "A" in data["cont"]

def test_app_realblocks_path():
    app = StateSpaceApp()
    req = RunRequest(form="expr", num="1", den="z**2 - 0.2*z + 0.9",
                     forms="diag,jordan", realblocks=True, check="off")
    res = app.run(req)
    assert "diag" in res.realizations and "jordan" in res.realizations
