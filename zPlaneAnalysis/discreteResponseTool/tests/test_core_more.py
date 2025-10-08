
import numpy as np
import math
from zPlaneAnalysis.discreteResponseTool import core as C

def test_poly_add_q_and_conv():
    a = np.array([1,2,3.0])
    b = np.array([1,-1.0])
    s = C.poly_add_q(a,b)
    assert s.tolist() == [2,1,3]
    c = C.poly_conv_q(a,b)
    # (1 + 2q + 3q^2)*(1 - q) = 1 + q + q^2 - 3q^3
    assert np.allclose(c, [1, 1, 1, -3])

def test_zpoly_from_q_and_roots_desc():
    q = np.array([2.0, 0.0, 0.0, 1.0])  # deg=3
    zdesc = C.zpoly_from_q(q, 3)
    assert zdesc.tolist() == [2.0,0.0,0.0,1.0]
    # roots_from_desc keeps zeros at origin with multiplicity
    r = C.roots_from_desc(np.array([1.0, 0.0, 0.0]))
    assert (r == 0).sum() == 2

def test_make_controller_paths_direct_digital():
    b,a,desc = C.make_controller_from_kwargs(ctrl_numz=[0.1,0.2], ctrl_denz=[1.0,-0.9])
    assert desc.startswith("Digital (direct)")
    assert b.shape[0]==2 and a.shape[0]==2

def test_make_controller_paths_digital_pid():
    b,a,desc = C.make_controller_from_kwargs(Kp=1.0, Ki=0.2, Kd=0.2)
    # numerator is length 3 for positional PID
    assert b.shape[0]==3 and a.shape[0]==2 and "PID" in desc

def test_make_controller_paths_analog_pid():
    b,a,desc = C.make_controller_from_kwargs(K=1.1, Ti=5.5, Td=0.18, T=1.0)
    assert a[0] == 1.0 and "Analog PID" in desc

def test_feedback_normalization_and_filt():
    num = np.array([0.5])
    den = np.array([1.0])
    tnum, tden = C.feedback_cl_q(num, den)
    y = C.filt_lti_q(tnum, tden, np.ones(8))
    assert np.isfinite(y).all() and y[-1] > 0

def test_step_metrics_all_fields():
    y = np.array([0.0, 0.4, 0.9, 1.1, 1.02, 1.0])
    m = C.step_metrics(y, tol=0.05)
    for k in ["final","peak","k_peak","overshoot_pct","k_rise_90pct","k_settle"]:
        assert k in m

def test_diophantine_place_simple():
    # Solve D*Ad + N*Bd = A_des ; D=1+q, N=1 ; A_des = (1 + 0.5q + 0.1q^2)
    D = np.array([1.0, 1.0])
    N = np.array([1.0])
    A = np.array([1.0, 0.5, 0.1])
    Bd, Ad = C.diophantine_place(N, D, A)
    # Reconstruct via polynomial convolution (not elementwise product)
    rec = C.poly_add_q(C.poly_conv_q(D, Ad), C.poly_conv_q(N, Bd))
    # Compare first len(A) coefficients
    rec = rec[:len(A)]
    assert np.allclose(rec, A, atol=1e-6)
