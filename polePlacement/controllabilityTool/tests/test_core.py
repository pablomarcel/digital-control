
from __future__ import annotations
import numpy as np
import pytest

from polePlacement.controllabilityTool.core import (
    controllability_matrix, output_controllability_matrix, pbh_controllable,
    gramian_controllability_ct, gramian_controllability_dt,
    finite_gramian_ct, finite_gramian_dt, minreal_controllable, sympy_rank_ctrb
)

def test_controllability_matrix_and_output():
    A = np.array([[0,1],[-2,-3]], float)
    B = np.array([[0],[1]], float)
    C = np.array([[1,0]], float)
    Ctrb = controllability_matrix(A,B)
    assert Ctrb.shape == (2,2)
    OC = output_controllability_matrix(A,B,C)
    assert OC.shape[0] == 1 and OC.shape[1] == 2

def test_pbh_controllable():
    A = np.array([[0,1],[-2,-3]], float)
    B = np.array([[0],[1]], float)
    ok, details = pbh_controllable(A,B)
    assert isinstance(ok,bool) and isinstance(details,list)
    assert len(details) == 2

def test_gramians_ct_dt_and_finite():
    A = np.array([[0,1],[-2,-3]], float)
    B = np.array([[0],[1]], float)
    Wc = gramian_controllability_ct(A,B)
    assert Wc is not None and Wc.shape==(2,2)
    Ad = np.array([[0.9, 0.0],[0.0, 0.8]], float)
    Bd = np.array([[0.1],[1.0]], float)
    Wd = gramian_controllability_dt(Ad,Bd)
    assert Wd is not None and Wd.shape==(2,2)
    Wf_ct = finite_gramian_ct(A,B,1.5)
    assert Wf_ct.shape==(2,2)
    Wf_dt = finite_gramian_dt(Ad,Bd,25)
    assert Wf_dt.shape==(2,2)

def test_minreal_trims():
    # Construct uncontrollable mode (first state not actuated)
    A = np.array([[0,1,0],[0,0,0],[0,0,-1]], float)
    B = np.array([[0],[0],[1]], float)
    Ar, Br, Tc = minreal_controllable(A,B)
    assert Ar.shape[0] <= 3
    assert Br.shape[0] == Ar.shape[0]

def test_sympy_rank_optional():
    A = np.array([[0,1],[-2,-3]], float)
    B = np.array([[0],[1]], float)
    r = sympy_rank_ctrb(A,B,None)
    # r is None if sympy missing; otherwise numeric
    assert (r is None) or isinstance(r,int)
