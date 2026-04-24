
import numpy as np
from rst_controllers.rstTool.design import Simulator

def test_simulator_with_delay_branch():
    A = np.array([1.0, -0.8]); B = np.array([0.5]); d = 1
    S = np.array([1.0, 0.0]); R = np.array([0.2]); T = np.array([1.0])
    sim = Simulator.simulate(A,B,d,R,S,T,N=30,r_step=1.0,v_step=0.1,v_k0=10,noise_sigma=0.0)
    assert len(sim.y) == 30 and sim.v[10] == 0.1

def test_simulator_no_delay_algebraic_loop():
    A = np.array([1.0, -0.4]); B = np.array([0.6]); d = 0
    S = np.array([1.0, 0.2]); R = np.array([0.1]); T = np.array([0.9])
    sim = Simulator.simulate(A,B,d,R,S,T,N=25,r_step=0.5,v_step=0.0,v_k0=0,noise_sigma=0.0)
    assert len(sim.u) == 25 and np.isfinite(sim.u).all()
