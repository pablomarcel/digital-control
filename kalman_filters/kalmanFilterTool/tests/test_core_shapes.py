
import numpy as np
from kalman_filters.kalmanFilterTool.core import default_cv_model, coerce_shapes

def test_default_cv_model_shapes():
    A,B,C,G,Q,R = default_cv_model(0.1, 0.25, 4.0)
    assert A.shape == (2,2) and B.shape == (2,1) and C.shape == (1,2)
    assert G.shape == (2,1) and Q.shape == (2,2) and R.shape == (1,1)

def test_coerce_state_form_q():
    dt=0.05
    A = np.array([[1,dt],[0,1.0]])
    B = np.array([[0.5*dt**2],[dt]])
    C = np.array([[1.0,0.0]])
    G = np.array([[0.5*dt**2],[dt]])
    Q = 0.5*np.eye(2)  # state-form
    R = np.array([[3.0]])
    model = coerce_shapes(A,B,C,G,Q,R,dt,0.25,False)
    assert model.noise_mode == "state"
    assert model.GQGT().shape == (2,2)

def test_coerce_input_form_q_and_row_G():
    dt=0.05
    A = np.array([[1,dt],[0,1.0]])
    B = np.array([[0.5*dt**2],[dt]])
    C = np.array([[1.0,0.0],[0.0,1.0]])  # p=2 to test R expansion later
    G_row = np.array([[0.0, 1.0]])       # auto-transpose to (2,1) is not possible here;
    # Instead craft proper G: row with 2 entries should become column (2,1)
    G = np.array([[0.0,1.0]])            # will be transposed inside
    Qw = np.array([[0.2,],[],[ ]], dtype=float) if False else np.array([[0.2]])  # keep shape (1,1)
    R = np.array([[5.0]])                # scalar 1x1 -> expands to 2x2
    model = coerce_shapes(A,B,C,G,Qw,R,dt,0.25,False)
    assert model.noise_mode == "input"
    assert model.G.shape[1] == 1  # transposed to (2,1)
    assert model.R.shape == (2,2) and np.isclose(model.R[0,0], 5.0)

def test_R_vector_and_diag_expansion():
    dt=0.05
    A = np.eye(2); B = np.ones((2,1)); C = np.eye(2); G = np.zeros((2,1))
    Q = np.eye(2); R = np.array([2.0, 3.0])  # vector -> diag
    model = coerce_shapes(A,B,C,G,Q,R,dt,0.25,False)
    assert model.R.shape == (2,2)
    assert np.isclose(model.R[0,0], 2.0) and np.isclose(model.R[1,1], 3.0)
