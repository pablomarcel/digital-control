
import sympy as sp
from system_design.juryTestTool.design import StabilityDesigner
from system_design.juryTestTool.core import Tolerances
from system_design.juryTestTool.io import poly_from_coeffs
from system_design.juryTestTool.apis import RunRequest
from system_design.juryTestTool.app import JuryTestApp

def test_stabilitydesigner_run_methods_eval_omega():
    # Use parametric 2nd-order and eval_K to traverse eval_summary + omega_d path
    z,K,P,a = poly_from_coeffs(["1","(0.3679*K - 1.3679)","(0.3679 + 0.2642*K)"], param_name="K")
    tol = Tolerances()
    des = StabilityDesigner(tol)
    subs = {K: 1.0}
    out, eval_summary = des.run_methods("all", P, a, z, K, subs_eval=subs, solve_range=True, T=1.0)
    assert "jury" in out and eval_summary is not None

def test_app_run_api_and_artifacts(tmp_path):
    req = RunRequest(coeffs="1, -1.2, 0.07, 0.3, -0.08", method="all", save_json="cov_app.json", save_table="cov_tables.txt")
    app = JuryTestApp()
    res = app.run(req)
    assert res.order == 4 and "jury" in res.methods
