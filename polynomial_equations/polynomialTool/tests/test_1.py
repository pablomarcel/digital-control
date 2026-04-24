import numpy as np
from polynomial_equations.polynomialTool.core import diophantine
def test_ogata_7_1_diophantine():
    A=[1,1,0.5]; B=[1,2]; D=[1,0,0,0]
    alpha,beta,E = diophantine(A,B,D,layout='ogata')
    assert np.allclose(alpha,[1.0,-1.2],atol=1e-6)
    assert np.allclose(beta,[0.2,0.3],atol=1e-6)
    assert E.shape==(4,4)
