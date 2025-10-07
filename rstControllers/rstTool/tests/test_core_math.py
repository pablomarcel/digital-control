
import numpy as np
from rstControllers.rstTool.core import (
    as_float_array, poly_conv, poly_add, poly_shift, poly_from_z_poles,
    deconv_poly_asc, eval_poly_at_one, stable_all
)

def test_poly_ops_and_roots():
    a = as_float_array([1, 2, 3])
    b = as_float_array([1, -1])
    c = poly_conv(a, b)
    assert np.allclose(c, np.convolve(a, b))
    s = poly_add(a, [1])
    assert s[0] == 2
    sh = poly_shift(a, 2)
    assert np.allclose(sh, [0,0,1,2,3])
    pz = poly_from_z_poles([0.5, 0.5])
    # (1 - 0.5 z^{-1})^2 in q-form equals 1 - 1*z^{-1} + 0.25 z^{-2}
    assert np.allclose(pz, [1.0, -1.0, 0.25], atol=1e-8)
    q, r = deconv_poly_asc(np.array([1.0, -1.0, 0.25]), np.array([1.0, -0.5]))
    assert np.allclose(np.convolve(q, [1.0, -0.5]) + r, [1.0, -1.0, 0.25])
    assert eval_poly_at_one([1,2,3]) == 6.0
    # Return type is numpy.bool_; assert truthiness, not identity
    assert bool(stable_all(np.array([0.2+0.1j, -0.4])))
