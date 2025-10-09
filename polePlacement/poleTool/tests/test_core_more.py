from __future__ import annotations
import numpy as np
from polePlacement.poleTool.core import (
    place_method, compute_K0, simulate_step, ctrb, obsv, pretty_poly_from_roots
)

def test_place_method_siso_fallback():
    # Even if SciPy/control aren't available, SISO path falls back to eigenvector method.
    A = np.array([[0, 1], [-0.16, -1]], dtype=complex)
    B = np.array([[0], [1]], dtype=complex)
    poles = np.array([0.4+0.4j, 0.4-0.4j], dtype=complex)
    K = place_method(A,B,poles)
    ev = np.linalg.eigvals(A - B@K)
    assert max(abs(np.sort_complex(ev) - np.sort_complex(poles))) < 1e-8

def test_k0_and_simulate_shapes():
    A = np.array([[0, 1], [-0.16, -1]], dtype=complex)
    B = np.array([[0], [1]], dtype=complex)
    C = np.array([[1, 0]], dtype=complex)
    poles = np.array([0.3+0.2j, 0.3-0.2j], dtype=complex)
    from polePlacement.poleTool.core import eigenvector_method_siso
    K = eigenvector_method_siso(A,B,poles)
    Acl = A - B@K
    K0,S,status = compute_K0(Acl,B,C)
    assert status in ("ok",) or "skipped" in status
    k, y = simulate_step(A,B,C,K,K0,N=25)
    assert len(k)==25 and y.shape==(1,25)

def test_ctrb_obsv_and_poly():
    A = np.array([[0,1],[-0.16,-1]], dtype=complex)
    B = np.array([[0],[1]], dtype=complex)
    C = np.array([[1,0]], dtype=complex)
    Mc = ctrb(A,B)
    Mo = obsv(A,C)
    assert Mc.shape == (2,2) and Mo.shape==(2,2)
    coeffs = pretty_poly_from_roots(np.linalg.eigvals(A))
    assert isinstance(coeffs, list) and len(coeffs)==3
