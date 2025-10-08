
from systemDesign.juryTestTool.apis import RunRequest, MethodResult, RunResult

def test_apis_dataclasses_roundtrip():
    req = RunRequest(coeffs="1, -1.2, 0.07, 0.3, -0.08", method="jury", solve_range=False)
    assert req.method == "jury"
    mr = MethodResult(verdict="STABLE", details={"foo":"bar"})
    res = RunResult(order=4, polynomial="z**4 - 1.2*z**3 + 0.07*z**2 + 0.3*z - 0.08",
                    coeffs_high_to_const=["1","-1.2","0.07","0.3","-0.08"],
                    parameter=None, methods={"jury": mr})
    assert "jury" in res.methods
