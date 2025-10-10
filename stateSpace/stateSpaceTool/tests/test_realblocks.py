
import numpy as np
from stateSpace.stateSpaceTool.core import jordan_or_diagonal, realify_complex_pairs

def test_realblocks_for_complex_pair():
    b = [1.0, 0.0, 0.0]
    a = [-0.2, 0.9]  # (z^2 - 0.2 z + 0.9)
    A,B,C,D,mult = jordan_or_diagonal(b,a)
    Ar,Br,Cr,Dr = realify_complex_pairs(A,B,C,D,mult,quiet=True)
    assert Ar.dtype == float and Br.dtype == float and Cr.dtype == float and Dr.dtype == float
