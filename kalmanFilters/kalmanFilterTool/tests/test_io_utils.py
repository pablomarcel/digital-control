
import os, sys, pathlib
import numpy as np
from kalmanFilters.kalmanFilterTool.io import parse_matrix, parse_vector
from kalmanFilters.kalmanFilterTool.utils import out_path, ensure_dir

def test_parse_matrix_basic_and_complex_tolerance():
    m = parse_matrix("1 2; 3 4")
    assert m.shape == (2,2)
    # Tiny imaginary parts get dropped
    m2 = parse_matrix("1+1e-15i 0; 0 2-1e-15i")
    assert np.allclose(m2, np.array([[1.0,0.0],[0.0,2.0]]))

def test_parse_vector_and_shape():
    v = parse_vector("1, 2, 3")
    assert v.shape == (3,1)
    assert float(v[1]) == 2.0

def test_out_path_relative_and_absolute(tmp_path):
    out_dir = tmp_path / "out"
    os.makedirs(out_dir, exist_ok=True)
    # relative -> under out_dir
    p1 = out_path(str(out_dir), "file.csv", "default.csv")
    assert pathlib.Path(p1).parent == out_dir
    # None -> default name
    p2 = out_path(str(out_dir), None, "default.csv")
    assert pathlib.Path(p2).name == "default.csv"
    # absolute path is honored
    abs_target = tmp_path / "abs" / "file.csv"
    p3 = out_path(str(out_dir), str(abs_target), "default.csv")
    assert pathlib.Path(p3) == abs_target
    assert abs_target.parent.exists()

def test_ensure_dir_creates_parents(tmp_path):
    target = tmp_path / "a" / "b" / "c.txt"
    ensure_dir(str(target))
    # now we can write
    with open(target, "w") as f:
        f.write("ok")
    assert target.exists()
