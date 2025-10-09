
from __future__ import annotations
import numpy as np

from polePlacement.transformationTool.apis import RunRequest
from polePlacement.transformationTool.app import TransformationApp
from polePlacement.transformationTool.core import controllability_matrix, observability_matrix

def test_ccf_basic_invariance():
    A = np.array([[0,1],[-2,-3]], dtype=complex)
    B = np.array([[0],[1]], dtype=complex)
    C = np.array([[1,0]], dtype=complex)

    req = RunRequest(A=A,B=B,C=C,to_ccf=True,check_invariance=True,pretty=False,name="t")
    res = TransformationApp().run(req)[0]

    # Eigenvalues preserved
    assert np.allclose(sorted(np.linalg.eigvals(A)), sorted(np.linalg.eigvals(res.Ahat)))

    # Controllability preserved
    rk0 = np.linalg.matrix_rank(controllability_matrix(A,B))
    rk1 = np.linalg.matrix_rank(controllability_matrix(res.Ahat,res.Bhat))
    assert rk0 == rk1

def test_ocf_basic_shapes():
    A = np.array([[0,1],[-2,-3]], dtype=complex)
    B = np.array([[0],[1]], dtype=complex)
    C = np.array([[1,5]], dtype=complex)

    req = RunRequest(A=A,B=B,C=C,to_ocf=True,pretty=False,name="t")
    res = TransformationApp().run(req)[0]
    # observable canonical Ahat must be similarity of A
    assert res.Ahat.shape == A.shape
    assert res.Chat.shape == C.shape
