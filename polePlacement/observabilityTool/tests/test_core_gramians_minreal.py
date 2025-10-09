
import numpy as np
from polePlacement.observabilityTool.core import (
    observability_matrix, rank_numeric, stable_ct, stable_dt,
    gramian_observability_ct, gramian_observability_dt,
    finite_gramian_ct, finite_gramian_dt, minreal_observable
)

def test_gramians_ct_dt_and_finite():
    # CT stable
    A_ct = np.array([[-1,0],[0,-2]], dtype=complex)
    C_ct = np.array([[1,0]], dtype=complex)
    assert stable_ct(A_ct) is True
    Wct = gramian_observability_ct(A_ct, C_ct)
    assert Wct is not None and Wct.shape == (2,2)

    # DT stable
    A_dt = 0.5*np.eye(2, dtype=complex)
    C_dt = np.array([[1,0]], dtype=complex)
    assert stable_dt(A_dt) is True
    Wdt = gramian_observability_dt(A_dt, C_dt)
    assert Wdt is not None and Wdt.shape == (2,2)

    # Finite
    Wf_ct = finite_gramian_ct(A_ct, C_ct, 1.5)
    assert Wf_ct.shape == (2,2)
    Wf_dt = finite_gramian_dt(A_dt, C_dt, 5)
    assert Wf_dt.shape == (2,2)

def test_minreal_unobservable_trims_state():
    # Classic unobservable pair: A has an unobservable mode due to C
    A = np.array([[0,1],[0,0]], dtype=complex)
    C = np.array([[1,0]], dtype=complex)
    Ar, Cr, T = minreal_observable(A, C, tol=1e-12)
    # This particular pair is observable; make unobservable by zero C
    A2 = np.array([[0,1],[0,0]], dtype=complex)
    C2 = np.array([[0,0]], dtype=complex)
    Ar2, Cr2, T2 = minreal_observable(A2, C2, tol=1e-12)
    assert Ar2.shape[0] == 0  # nothing observable
