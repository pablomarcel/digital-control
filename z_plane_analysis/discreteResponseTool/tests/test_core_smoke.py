
import numpy as np
from z_plane_analysis.discreteResponseTool.core import zroots_from_q, filt_lti_q, series_q, feedback_cl_q

def test_zroots_origin_multiplicity():
    roots = zroots_from_q(np.array([1.0, 0.0, 0.0]))
    assert (roots == 0).sum() == 2

def test_feedback_series_identity():
    num, den = series_q(np.array([1.0]), np.array([1.0]), np.array([1.0]), np.array([1.0]))
    tnum, tden = feedback_cl_q(num, den)
    y = filt_lti_q(tnum, tden, np.ones(5))
    assert np.isfinite(y).all()
