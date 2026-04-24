
import numpy as np
from state_space.stateSpaceTool.core import controllable_canonical, observable_canonical

def test_cont_obs_duality_shapes():
    b = [0,1,1]
    a = [1.3, 0.4]
    Ac,Bc,Cc,Dc = controllable_canonical(b,a)
    Ao,Bo,Co,Do = observable_canonical(b,a)
    n = len(a)
    assert Ac.shape == (n,n) and Bc.shape == (n,1) and Cc.shape == (1,n) and Dc.shape == (1,1)
    assert Ao.shape == (n,n) and Bo.shape == (n,1) and Co.shape == (1,n) and Do.shape == (1,1)
