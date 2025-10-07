
import sys, types, numpy as np
from kalmanFilters.kalmanFilterTool.core import dare_estimation

def test_dare_estimation_fallback_branch():
    # Craft small system
    A = np.eye(2)
    C = np.array([[1.0, 0.0]])
    Q = np.eye(2)*0.1
    R = np.array([[1.0]])

    # Insert dummy scipy that lacks linalg to force fallback path
    class DummySciPy(types.ModuleType):
        pass
    sys.modules["_orig_scipy"] = sys.modules.get("scipy")
    sys.modules["scipy"] = DummySciPy("scipy")
    try:
        P = dare_estimation(A,C,Q,R)
        assert P.shape == (2,2)
    finally:
        # Restore
        if sys.modules.get("_orig_scipy") is not None:
            sys.modules["scipy"] = sys.modules["_orig_scipy"]
            del sys.modules["_orig_scipy"]
        else:
            del sys.modules["scipy"]
