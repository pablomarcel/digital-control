
import numpy as np
from state_space.stateSpaceTool.app import StateSpaceApp
from state_space.stateSpaceTool.apis import RunRequest

def test_app_example_ogata_5_1():
    app = StateSpaceApp()
    req = RunRequest(form="expr", num="z + 1", den="z**2 + 1.3*z + 0.4", forms="cont,obs,diag,jordan", check="brief")
    res = app.run(req)
    assert "cont" in res.realizations
    A = np.array(res.realizations["cont"]["A"], dtype=float)
    assert A.shape == (2,2)
    # last row equals [-a2, -a1] = [-0.4, -1.3]
    assert np.allclose(A[-1, :].tolist(), [-0.4, -1.3], atol=1e-9)
    assert res.check_log.startswith("[check]")
