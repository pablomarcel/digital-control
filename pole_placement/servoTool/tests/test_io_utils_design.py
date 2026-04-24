from __future__ import annotations
import os, numpy as np, json, math
import pytest
from pole_placement.servoTool import io as iox
from pole_placement.servoTool.utils import out_path
from pole_placement.servoTool.design import servo_eqs, observer_eqs, emit_equations

def test_parse_matrix_and_force_col():
    M = iox.parse_matrix("1 2; 3 4")
    assert M.shape == (2,2)
    v = iox.parse_matrix("1 2 3")
    vt = iox.force_col(v)
    assert vt.shape == (3,1)
    c = iox.parse_matrix("1/2 1/3; 1/4 1/5")
    assert float(c[0,0]) == 0.5

def test_parse_poles_complex_real():
    poles = iox.parse_poles("0.5, 0.6, -0.1+0.2j, -0.1-0.2j")
    assert len(poles) == 4
    assert poles[0].real == pytest.approx(0.5)

def test_out_path_basename():
    p = out_path("foo.json")
    assert p.endswith(os.path.join("pole_placement","servoTool","out","foo.json"))

def test_emit_equations_strings(tmp_path):
    G = np.eye(2); H = np.ones((2,1)); C = np.array([[1,0]])
    K1 = np.array([[1.0]]); K2 = np.array([[0.1, 0.2]])
    lines = servo_eqs(G,H,C,K1,K2) + observer_eqs("prediction",(1,1))
    text = emit_equations(lines, None, True)
    assert "u(k) =" in text and "xi_hat_b" in text

def test_yaml_optional_missing(monkeypatch, tmp_path):
    # If PyYAML is missing, load_yaml should raise; simulate by monkeypatching module attr
    import pole_placement.servoTool.io as mod
    yaml_saved = getattr(mod, "yaml", None)
    try:
        mod.yaml = None
        with pytest.raises(RuntimeError):
            mod.load_yaml(str(tmp_path/"x.yaml"))
    finally:
        mod.yaml = yaml_saved
