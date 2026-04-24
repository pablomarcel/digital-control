import os
import json
import sympy as sp
from system_design.juryTestTool.io import poly_from_coeffs, load_from_json, dump_json, dump_table
from system_design.juryTestTool.utils import in_path, out_path, sstr, fmt_row, fmt_vec, banner

def _pp(title, obj):
    print("\n=== {} ===".format(title))
    print("type:", type(obj))
    print("repr:", repr(obj))
    try:
        print("str :", str(obj))
    except Exception as e:
        print("str failed:", e)

def test_poly_from_coeffs_and_utils_rational(tmp_path):
    print("\n[TEST] poly_from_coeffs (rational=True) + utils formatting")
    z, K, P, a = poly_from_coeffs(["1","1/2","1/3"], var_name="z", rational=True)

    _pp("symbol z", z)
    _pp("param K", K)
    _pp("polynomial P", P)
    _pp("coeffs a (high->const)", a)

    # Polynomial shape
    assert str(P) == "z**2 + z/2 + 1/3"

    # No param expected here
    assert K is None

    # banner() is a title + dashed line (not ===). Be explicit and noisy.
    btxt = banner("hi")
    _pp("banner('hi')", btxt)
    assert "hi" in btxt, "banner should include title"
    assert "-" * 5 in btxt, "banner should include a dashed underline"

    # Formatting helpers
    fv = fmt_vec([1,2])
    fr = fmt_row("Row:", [1,2])
    _pp("fmt_vec([1,2])", fv)
    _pp("fmt_row('Row:', [1,2])", fr)
    assert fv == "1  2"
    assert fr.startswith("Row:"), f"Unexpected fmt_row prefix: {fr!r}"

    # sstr on rationals should be a short float (6g). Tolerate either 0.333333 or 0.333333...
    s = sstr(sp.Rational(1,3))
    _pp("sstr(1/3)", s)
    assert s.startswith("0.33333"), f"sstr(1/3) unexpected: {s!r}"

def test_load_and_dump_json_roundtrip(tmp_path):
    print("\n[TEST] load_from_json + dump_json/dump_table + in/out paths")
    # prepare json in package in/
    ipath = in_path("tmp_ex.json")
    payload = {"variable":"z","coeffs":["1","-1","0.5"]}
    print("Writing JSON to:", ipath)
    ipath.write_text(json.dumps(payload))
    z,K,P,a = load_from_json("tmp_ex.json", rational=False)
    _pp("loaded polynomial", P)
    _pp("loaded coeffs a", a)
    assert K is None and a[0] == 1

    # dump artifacts
    pjson = dump_json({"ok":True}, "tmp_out.json")
    ptab  = dump_table("hello", "tmp_out.txt")
    print("dump_json path:", pjson)
    print("dump_table path:", ptab)

    # Verify locations resolve under package ./out/
    op_json = out_path("tmp_out.json")
    op_txt  = out_path("tmp_out.txt")
    print("resolved out json:", op_json)
    print("resolved out txt :", op_txt)

    assert os.path.exists(op_json), "JSON not found in out/"
    assert os.path.exists(op_txt),  "TXT not found in out/"
    assert pjson.endswith("tmp_out.json") and ptab.endswith("tmp_out.txt")
