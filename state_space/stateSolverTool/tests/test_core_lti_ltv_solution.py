
import sympy as sp
from state_space.stateSolverTool.core import lti_solution, z_transform_block, brief_check_lti, brief_check_ltv

def test_lti_solution_shapes_and_checker():
    k = sp.symbols('k', integer=True)
    G = sp.Matrix([[0,1],[-sp.Rational(4,25), -1]])
    H = sp.Matrix([[1],[1]])
    C = sp.Matrix([[1,0]])
    D = sp.Matrix([[0]])
    x0 = sp.Matrix([[1],[-1]])
    u_expr = sp.Integer(1)
    Psi, xk, yk = lti_solution(G,H,C,D,x0,u_expr,k, power_style="rational")
    assert Psi.shape == (2,2) and xk.shape == (2,1)
    status = brief_check_lti(G,H,C,D,x0,u_expr,Psi,xk,yk, steps=3)
    assert status == "ok."

def test_z_transform_block_for_geometric_and_step():
    z = sp.symbols('z')
    k = sp.symbols('k', integer=True)
    G = sp.eye(1)
    H = sp.Matrix([[1]])
    C = sp.Matrix([[1]])
    D = sp.Matrix([[0]])
    x0 = sp.Matrix([[0]])
    lines_step = z_transform_block(G,H,C,D,x0, sp.Integer(1), z)
    assert any("U(z) = \\frac{z}{z - 1}" in L for L in lines_step)
    lines_geo = z_transform_block(G,H,C,D,x0, (sp.Rational(9,10))**k, z)
    assert any("0.9" in L or "9" in L for L in lines_geo)

def test_ltv_checker_phi_and_sequences():
    k = sp.symbols('k', integer=True)
    Gk = sp.Matrix([[1,1],[0,1]])
    Hk = sp.Matrix([[0],[0]])
    Ck = sp.Matrix([[1,0]])
    Dk = sp.Matrix([[0]])
    x0 = sp.Matrix([[0],[0]])
    u_expr = sp.Integer(0)
    status, Phi, xs, ys = brief_check_ltv(Gk,Hk,Ck,Dk,x0,u_expr, steps=3)
    assert status == "ok." and Phi.shape == (2,2) and len(xs) == 4
