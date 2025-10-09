import os, json, numpy as np, importlib, pytest
import quadraticControl.quadraticTool.utils as utils

def test_utils_pkg_path_exists():
    p = utils.pkg_path("in","ex8_1.yaml")
    assert os.path.exists(p)

def test_utils_np_serialization_roundtrip():
    # Only run if the helpers exist; otherwise skip cleanly.
    np_to_native = getattr(utils, "np_to_native", None)
    native_to_np = getattr(utils, "native_to_np", None)
    if np_to_native is None or native_to_np is None:
        pytest.skip("np_to_native/native_to_np not present in utils; skipping roundtrip test.")
    data = {"A": np.array([[1.0,2.0],[3.0,4.0]]), "x": np.array([1.0,2.0])}
    native = np_to_native(data)
    s = json.dumps(native)
    back_native = json.loads(s)
    back = native_to_np(back_native)
    assert np.allclose(back["A"], data["A"]) and np.allclose(back["x"], data["x"])

def test_cli_import_smoke():
    # Import CLI module (no execution)
    mod = importlib.import_module("quadraticControl.quadraticTool.cli")
    assert hasattr(mod, "__file__")
