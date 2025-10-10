import sympy as sp
from stateSpace.liapunovTool.io import parse_matrix
from stateSpace.liapunovTool.core import PDClassifier

def test_parse_matrix_variants():
    a = parse_matrix("[[1 2]; [3 4]]")
    b = parse_matrix("[[1, 2]; [3, 4]]")
    c = parse_matrix("[[1,2],[3,4]]")
    assert a == b == c == sp.Matrix([[1,2],[3,4]])

def test_pd_classifier_positive_definite():
    P = sp.Matrix([[2, 0], [0, 3]])
    assert PDClassifier.sylvester_pd(P) == "positive definite"
