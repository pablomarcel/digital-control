from __future__ import annotations
import numpy as np
from polePlacement.poleTool.core import (
    ackermann_siso, eigenvector_method_siso, place_method,
    pretty_poly_from_roots, match_pole_sets
)

def test_ackermann_matches_poles():
    A = np.array([[0, 1], [-0.16, -1]], dtype=complex)
    B = np.array([[0], [1]], dtype=complex)
    poles = np.array([0.5+0.5j, 0.5-0.5j], dtype=complex)
    K = ackermann_siso(A,B,poles)
    ev = np.linalg.eigvals(A - B@K)
    assert match_pole_sets(ev, poles) < 1e-9

def test_eigenvector_method():
    A = np.array([[0, 1], [-0.16, -1]], dtype=complex)
    B = np.array([[0], [1]], dtype=complex)
    poles = np.array([0.4+0.3j, 0.4-0.3j], dtype=complex)
    K = eigenvector_method_siso(A,B,poles)
    ev = np.linalg.eigvals(A - B@K)
    assert match_pole_sets(ev, poles) < 1e-9
