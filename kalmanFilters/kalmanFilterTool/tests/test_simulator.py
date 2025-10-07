
import numpy as np
from kalmanFilters.kalmanFilterTool.core import default_cv_model, coerce_shapes, Simulator

def _basic_model(dt=0.05, q=0.2, r=4.0):
    A,B,C,G,Q,R = default_cv_model(dt,q,r)
    model = coerce_shapes(A,B,C,G,Q,R, dt, q, True)  # Q came from defaults
    return model

def test_simulator_time_varying_shapes():
    model = _basic_model()
    n, p = model.n, model.p
    sim = Simulator(model, dt=0.05, T=0.2, seed=123, steady=False, u=0.1)
    x0 = np.zeros((n,1)); P0 = np.eye(n)*10; xtrue0 = np.zeros((n,1))
    res = sim.run(x0,P0,xtrue0)
    assert res.t.ndim == 1 and res.X_true.shape[0] == n
    assert res.Y_meas.shape[0] == p
    assert res.K_gain is not None
    assert np.isfinite(res.X_hat).all()

def test_simulator_steady_state_gain_present():
    model = _basic_model()
    n, p = model.n, model.p
    sim = Simulator(model, dt=0.05, T=0.2, seed=1, steady=True, u=0.0)
    res = sim.run(np.zeros((n,1)), np.eye(n)*10, np.zeros((n,1)))
    # In steady mode, K_gain should be the final used K (Kss)
    assert res.K_gain is not None
    assert res.K_gain.shape[0] == n and res.K_gain.shape[1] == p
