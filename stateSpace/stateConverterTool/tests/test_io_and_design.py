from __future__ import annotations
import os, pytest
import sympy as sp
from stateSpace.stateConverterTool.io import parse_matrix, parse_scalar, ensure_out_dir
from stateSpace.stateConverterTool.design import fmt, fmt_matrix, build_latex

def test_parse_matrix_and_scalar_and_ensure_out_dir(tmp_path):
    M = parse_matrix("[[1, 2],[3, 4]]")
    assert M.shape == (2,2) and int(M[1,0]) == 3
    s = parse_scalar("1/3")
    assert s == sp.Rational(1,3)
    out_file = tmp_path / "nested" / "file.txt"
    p = ensure_out_dir(str(out_file))
    assert os.path.dirname(p).endswith("nested")

def test_formatters_and_latex():
    A=sp.eye(1); B=sp.ones(1,1); C=sp.ones(1,1); D=sp.zeros(1,1)
    T=sp.Symbol('T')
    G=sp.eye(1); H=sp.ones(1,1); Finv=None; F=sp.ones(1,1)
    assert fmt_matrix(sp.eye(2)) == "[[1, 0]; [0, 1]]"
    assert fmt(sp.Matrix([[42]])) == "42"
    latex = build_latex(A,B,C,D,T,G,H,Finv,F)
    assert "F(z)" in latex and "G(T)" in latex
 
def test_parse_matrix_errors():
    with pytest.raises(ValueError):
        parse_matrix("not a matrix")
    with pytest.raises(ValueError):
        parse_matrix("[1,2,3]")
