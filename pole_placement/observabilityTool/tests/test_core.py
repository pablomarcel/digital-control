
import numpy as np
from pole_placement.observabilityTool.core import observability_matrix, rank_numeric, pbh_observable

def test_obsv_rank_observable_2x2():
    A = np.array([[-1, 0],[0,-2]], dtype=complex)
    C = np.array([[1, 5]], dtype=complex)
    O = observability_matrix(A, C)
    assert rank_numeric(O) == 2

def test_pbh_unobservable_changes_with_C():
    A = np.array([[0,1,0],[0,0,1],[-6,-11,-6]], dtype=complex)
    C = np.array([[4,5,1]], dtype=complex)
    ok, details = pbh_observable(A, C)
    assert ok is False
