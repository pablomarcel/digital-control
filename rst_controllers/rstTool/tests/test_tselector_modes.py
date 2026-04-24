
import numpy as np
from rst_controllers.rstTool.design import TSelector

def test_tselector_unity_dc_no_integrator():
    B = np.array([0.5])
    Acl = np.array([1.0, -1.2, 0.36])
    T = TSelector.choose('unity_dc', B, Acl, None, None, None, False, np.array([1.0]))
    # Gain = Acl(1)/B(1) = (1-1.2+0.36)/0.5 = 0.16/0.5 = 0.32
    assert abs(T[0] - 0.32) < 1e-8

def test_tselector_unity_dc_with_integrator():
    T = TSelector.choose('unity_dc', np.array([0.5]), np.array([1.0]), None, None, None, True, np.array([0.2,0.8]))
    assert abs(T[0] - 1.0) < 1e-8  # R(1)=1.0

def test_tselector_ac_manual_and_errors():
    Acl = np.array([1.0, -1.2, 0.36])
    Ao = np.array([1.0])
    B = np.array([0.5])
    # Derive Ac from Acl/Ao
    T = TSelector.choose('ac', B, Acl, None, Ao, None, False, np.array([1.0]))
    assert T.ndim == 1
    # Manual path
    Tm = TSelector.choose('manual', B, Acl, None, None, np.array([1.23, 0.0]), False, np.array([1.0]))
    assert np.allclose(Tm, [1.23, 0.0])
