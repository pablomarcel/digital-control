
from __future__ import annotations
import numpy as np
import pytest

from polePlacement.transformationTool.core import (
    realify_if_close, controllability_matrix, observability_matrix,
    charpoly_coeffs, W_from_a, to_ccf, to_ocf, to_diag, to_jordan_sympy,
    siso_tf_coeffs
)

def test_realify_if_close_and_ranks():
    A = np.array([[0,1],[-2,-3]], dtype=complex)
    B = np.array([[0],[1]], dtype=complex)
    C = np.array([[1,0]], dtype=complex)
    assert realify_if_close(A).dtype == float
    Mc = controllability_matrix(A,B)
    No = observability_matrix(A,C)
    assert Mc.shape == (2,2) and No.shape == (2,2)

def test_charpoly_and_W():
    A = np.array([[0,1],[-2,-3]], dtype=complex)
    a = charpoly_coeffs(A)  # returns [a1, a2]
    W = W_from_a(a)
    assert W.shape == (2,2)

def test_to_ccf_errors_and_success():
    A = np.array([[0,1],[-2,-3]], dtype=complex)
    B_bad = np.array([[1,0],[0,1]], dtype=complex)  # not SISO
    with pytest.raises(ValueError):
        to_ccf(A, B_bad, None, None)
    # uncontrollable case
    A2 = np.array([[0,0],[0,0]], dtype=complex)
    B2 = np.array([[0],[0]], dtype=complex)
    with pytest.raises(ValueError):
        to_ccf(A2, B2, None, None)
    # success
    B = np.array([[0],[1]], dtype=complex); C = np.array([[1,0]], dtype=complex)
    Ah,Bh,Ch,Dh,T,a = to_ccf(A,B,C,None)
    assert Ah.shape == (2,2) and Bh.shape == (2,1)

def test_to_ocf_errors_and_success():
    A = np.array([[0,1],[-2,-3]], dtype=complex)
    B = np.array([[0],[1]], dtype=complex)
    Cbad = np.array([[1,0],[0,1]], dtype=complex)  # not 1xn
    with pytest.raises(ValueError):
        to_ocf(A, B, Cbad, None)
    C = np.array([[1,5]], dtype=complex)
    Ah,Bh,Ch,Dh,Q,a = to_ocf(A,B,C,None)
    assert Ah.shape == (2,2) and Ch.shape == (1,2)

def test_to_diag_and_failure_on_repeated_eigs():
    A = np.array([[1,0],[0,2]], dtype=complex)
    B = np.array([[0],[1]], dtype=complex)
    C = np.array([[1,0]], dtype=complex)
    Ah,Bh,Ch,Dh,P = to_diag(A,B,C,None)
    assert np.allclose(np.diag(Ah), [1,2])
    # repeated eigenvalue -> expect failure
    Arep = np.array([[1,1],[0,1]], dtype=complex)
    with pytest.raises(ValueError):
        to_diag(Arep, B, C, None)

def test_to_jordan_sympy_success():
    # Simple Jordan (nilpotent)
    A = np.array([[0,1,0],[0,0,1],[0,0,0]], dtype=complex)
    B = np.array([[0],[0],[1]], dtype=complex)
    C = np.array([[1,0,0]], dtype=complex)
    J,Bh,Ch,Dh,S = to_jordan_sympy(A,B,C,None)
    assert J.shape == (3,3) and S.shape == (3,3)

def test_siso_tf_coeffs_errors_and_norm():
    A = np.array([[0,1],[-2,-3]], dtype=complex)
    B = np.array([[0],[1]], dtype=complex)
    C = np.array([[1,0]], dtype=complex)
    b,a = siso_tf_coeffs(A,B,C,None)
    assert isinstance(a, np.ndarray) and isinstance(b, np.ndarray)
    # non-SISO
    with pytest.raises(ValueError):
        siso_tf_coeffs(A, np.array([[1,0],[0,1]], dtype=complex), C, None)
