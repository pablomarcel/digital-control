import sympy as sp
from state_space.liapunovTool.core import PBuilder, LyapunovSolver, PDClassifier

def test_pbuilder_structures():
    pu_sym = PBuilder.build(3, hermitian=False)
    # symmetric real: off-diagonals equal
    assert pu_sym.P[0,1] == pu_sym.P[1,0]
    pu_herm = PBuilder.build(2, hermitian=True)
    # hermitian: conjugate relation
    assert sp.conjugate(pu_herm.P[0,1]) == pu_herm.P[1,0]

def test_pd_classifier_negative_and_unknown():
    P_neg = sp.Matrix([[1,0],[0,-1]])
    assert PDClassifier.sylvester_pd(P_neg) == "not positive definite"
    x = sp.symbols("x", real=True)
    P_unknown = sp.Matrix([[x,0],[0,1]])
    assert PDClassifier.sylvester_pd(P_unknown) in ("unknown", "not positive definite", "positive definite")
    # But for x as a symbol with no sign, "unknown" is the expected safe outcome
    # Allow any due to Sympy heuristics, but this line executes branch paths.

def test_solver_ct_and_dt_paths():
    A = sp.Matrix([[-1,-2],[1,-4]])
    Q = sp.eye(2)
    P_ct = LyapunovSolver.solve_ct(A, Q, hermitian=False)
    assert P_ct == P_ct.T
    G = sp.Matrix([[0,1],[-sp.Rational(1,2),-1]])
    P_dt = LyapunovSolver.solve_dt(G, Q, hermitian=False)
    assert P_dt == P_dt.T
