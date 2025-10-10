
import sympy as sp
from stateSpace.stateSolverTool.design import lti_latex_block
from stateSpace.stateSolverTool.core import inverse_zI_minus_G

def test_lti_latex_block_includes_sections():
    z = sp.symbols('z')
    G = sp.Matrix([[0,1],[-sp.Rational(4,25), -1]])
    H = sp.Matrix([[1],[1]])
    C = sp.Matrix([[1,0]])
    D = sp.Matrix([[0]])
    x0 = sp.Matrix([[1],[-1]])
    u_expr = sp.Integer(1)
    inv, det, adj, a, Hs = inverse_zI_minus_G(G, z)
    lines = lti_latex_block(G,H,C,D,x0,u_expr, inv, z, sp.eye(2), x0, sp.Matrix([[0]]), real_modal=None, include_zt=True)
    text = "\n".join(lines)
    assert "LTI system" in text and "zI - G" in text and "\Psi(k)" in text
