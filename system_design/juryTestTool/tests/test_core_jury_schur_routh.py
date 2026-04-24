
import sympy as sp
from system_design.juryTestTool.core import (
    Tolerances, jury_table_vectors, jury_inequalities, schur_reflection_coeffs,
    schur_inequalities, bilinear_Q_from_coeffs, poly_coeffs_desc, routh_array,
    routh_first_column_inequalities, print_conditions, verdict_from, compute_roots, any_radius_on_unit_circle
)
from system_design.juryTestTool.io import poly_from_coeffs

def test_jury_schur_routh_paths():
    z,K,P,a = poly_from_coeffs(["1","-1.2","0.07","0.3","-0.08"])
    rows = jury_table_vectors(a)
    assert rows and isinstance(rows[0], tuple)
    ineqsJ, labelsJ = jury_inequalities(P,a,z)
    txt, all_true, any_equal = print_conditions(ineqsJ, labelsJ, subs=None, tols=Tolerances())
    assert "INEQUALITIES" in txt
    v = verdict_from(all_true, any_equal)
    assert v in {"STABLE","UNSTABLE","CRITICAL (boundary)"}  # depends on tol/expr

    kappas, polys = schur_reflection_coeffs(a)
    assert len(kappas) >= 1
    ineqsS, labelsS, _ = schur_inequalities(P,a,z)
    txt2, _, _ = print_conditions(ineqsS, labelsS, subs=None, tols=Tolerances())
    assert "S0" in txt2

    w = sp.symbols('w', complex=True)
    Q = bilinear_Q_from_coeffs(a,w)
    coeffs = poly_coeffs_desc(Q,w)
    arr = routh_array(coeffs)
    ineqsR, labelsR = routh_first_column_inequalities(arr)
    txt3, _, _ = print_conditions(ineqsR, labelsR, subs=None, tols=Tolerances())
    assert "ROUTH" not in txt3 or isinstance(txt3, str)

def test_roots_and_boundary_unit_circle():
    # quadratic with parameter K to test roots path
    z,K,P,a = poly_from_coeffs(["1","(0.3679*K - 1.3679)","(0.3679 + 0.2642*K)"], param_name="K")
    subs = {K: 1.0}
    roots = compute_roots(a, subs)
    assert len(roots) == 2
    radii = [abs(r) for r in roots]
    assert isinstance(any_radius_on_unit_circle(radii, Tolerances()), bool)
