import os
import pytest
import sympy as sp
from stateSpace.liapunovTool.design import fmt, make_ct_latex, make_dt_latex
from stateSpace.liapunovTool.io import parse_matrix, save_text, out_path

def test_fmt_and_latex_blocks(tmp_path):
    M = sp.Matrix([[1,2],[3,4]])
    s = fmt(M)
    assert "[[1, 2]; [3, 4]]" in s
    ct = make_ct_latex(M, sp.eye(2), M, hermitian=False)
    dt = make_dt_latex(M, sp.eye(2), M, hermitian=True)
    assert "Continuous-time" in ct and "Discrete-time" in dt

def test_io_out_path_and_save_text(tmp_path):
    rel = out_path(str(tmp_path), "a/b/c.txt")
    save_text(rel, "hello")
    assert os.path.exists(rel)
    abs_path = tmp_path / "abs.txt"
    save_text(str(abs_path), "world")
    assert abs_path.exists()

def test_parse_matrix_errors():
    with pytest.raises(ValueError):
        parse_matrix("[[1,2]; [3]]")  # inconsistent row lengths
