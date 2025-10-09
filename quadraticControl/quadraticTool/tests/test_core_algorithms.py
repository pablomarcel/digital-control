import numpy as np
from quadraticControl.quadraticTool.core import (
    FiniteHorizonLQR, CTtoDTWeights, SteadyStateLQR, ServoLQR, LyapunovAnalyzer
)

def test_fh_lqr_shapes():
    G = np.array([[0.9]]); H = np.array([[0.1]])
    Q = np.array([[1.0]]); R = np.array([[0.5]])
    S = np.array([[1.0]]); M = np.array([[0.0]])
    x0 = np.array([1.0]); N=5
    res = FiniteHorizonLQR().solve(G,H,Q,R,N,S,M,x0)
    assert len(res.K_seq)==N and len(res.x_seq)==N+1 and len(res.u_seq)==N

def test_ct_to_dt_weights_and_ss_lqr():
    a,b,T = -1.0, 1.0, 0.1
    disc = CTtoDTWeights().siso_ogata(a,b,T)
    assert disc.G.shape==(1,1) and disc.H.shape==(1,1)
    res = SteadyStateLQR().solve(disc.G, disc.H, disc.Q1, disc.R1)
    assert res.P.shape==(1,1) and res.K.shape==(1,1)

def test_servo_and_lyap():
    G = np.array([[0.9, 0.1],[0.0, 1.0]])
    H = np.array([[0.1],[0.05]])  # nonzero second entry for stabilizability
    C = np.array([[1.0, 0.0]])
    Qx = np.eye(2)
    Qi = np.array([[0.5]])
    R = np.array([[0.1]])
    sres = ServoLQR().solve(G,H,C,Qx,Qi,R)
    assert sres.P.shape==(3,3) and sres.K_full.shape==(1,3)
    Gs = np.array([[0.9, 0.0],[0.0, 0.8]]); Q = np.eye(2)
    lres = LyapunovAnalyzer().solve(Gs,Q,None)
    assert lres.P.shape==(2,2)
