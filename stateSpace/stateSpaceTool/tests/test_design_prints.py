
import numpy as np
from stateSpace.stateSpaceTool.design import pretty_tf_lines, latex_tf, pretty_ss_lines
from stateSpace.stateSpaceTool.core import controllable_canonical

def test_pretty_and_latex_tf_lines():
    b = [0,1,1]
    a = [1.3,0.4]
    zm1, zdom = pretty_tf_lines(b,a)
    assert "z" in zm1 and "z" in zdom
    L1, L2 = latex_tf(b,a)
    assert "\\frac" in L1 and "\\frac" in L2

def test_pretty_ss_lines_from_ccf():
    b = [0,1,1]
    a = [1.3,0.4]
    A,B,C,D = controllable_canonical(b,a)
    xline, yline = pretty_ss_lines(A,B,C,D)
    assert "x(k+1)" in xline and "y(k)" in yline
