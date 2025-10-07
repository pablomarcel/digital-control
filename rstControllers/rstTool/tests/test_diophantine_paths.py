
import numpy as np
from rstControllers.rstTool.core import DiophantineSolver

def test_recommended_degrees_alloc_variants():
    A = np.array([1.0, -0.8])
    B = np.array([0.5])
    d = 1
    Acl = np.array([1.0, -1.2, 0.36])
    ds, dr = DiophantineSolver.recommended_degrees(A, B, d, Acl, integrator=False, alloc='S')
    ds_r, dr_r = DiophantineSolver.recommended_degrees(A, B, d, Acl, integrator=False, alloc='R')
    # For this small example, both should be >=0
    assert ds >= 0 and dr >= 0 and ds_r >= 0 and dr_r >= 0

def test_solve_with_overrides_and_integrator():
    A = np.array([1.0, -0.8])
    B = np.array([0.5])
    d = 1
    Acl = np.array([1.0, -1.2, 0.36, 0.0])  # pad to exercise row cover
    S, R = DiophantineSolver.solve(A, B, d, Acl, degS=3, degR=2, integrator=True, alloc='S')
    # Requested degrees are honored via padding
    assert len(S) == 4  # degS=3 -> 4 coeffs
    assert len(R) == 3  # degR=2 -> 3 coeffs
