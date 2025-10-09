import numpy as np, sys, os, logging, traceback
from polynomialEquations.polynomialTool.core import (
    diophantine, sylvester_matrix_desc, convmtx_desc,
    factor_z_from_F_and_update_d, ogata_sylvester_E, dlsim_safe
)
from scipy.signal import dlti

# Crank logging globally
logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s] %(name)s:%(lineno)d: %(message)s", stream=sys.stdout)

def test_factor_z_updates_delay():
    print("\\n[TEST] test_factor_z_updates_delay")
    k, F2, d2 = factor_z_from_F_and_update_d([1,0,0], 0)
    print(f"[DBG] k={k}, F2={F2}, d2={d2}")
    assert k==2 and F2==[1] and d2==2

def test_sylvester_and_convmtx_shapes():
    print("\\n[TEST] test_sylvester_and_convmtx_shapes")
    EA = convmtx_desc([1,2,3], 2)
    E  = sylvester_matrix_desc([1,1], [1,0.5], 1, 1, d=1)
    print(f"[DBG] EA.shape={EA.shape}, E.shape={E.shape}")
    assert EA.shape == (4,2)
    assert E.shape[1] == 2  # Ls+Lr

def test_diophantine_desc_square():
    print("\\n[TEST] test_diophantine_desc_square")
    A=[1, -1]   # degree 1 (n=1) -> degR=0
    B=[1]       # m=0, with d=1 -> degS = 0
    D=[1, 0]    # length 2 to match rows
    print(f"[DBG] INPUTS: A={A}, B={B}, D={D}, d=1, layout='desc'")
    S,R,E = diophantine(A,B,D,d=1,layout='desc')
    print(f"[DBG] OUTPUTS: S={S}, R={R}, E.shape={E.shape}")
    assert len(S)==1 and len(R)==1
    assert E.shape[0] == E.shape[1]

def test_diophantine_desc_lstsq():
    print("\\n[TEST] test_diophantine_desc_lstsq")
    A=[1, 0.5, 0.25]  # n=2 -> degR default 1
    B=[1]             # m=0, d=0 -> degS default max(0,-1)=0 after patch
    D=[1]
    print(f"[DBG] INPUTS: A={A}, B={B}, D={D}, d=0, layout='desc'")
    try:
        S,R,E = diophantine(A,B,D,d=0,layout='desc')
        print(f"[DBG] OUTPUTS: S={S}, R={R}, E.shape={E.shape}")
        assert len(R)>=1 and len(S)>=1
    except Exception as e:
        print("[ERR] Exception in test_diophantine_desc_lstsq:", repr(e))
        traceback.print_exc()
        raise

def test_ogata_sylvester_shape():
    print("\\n[TEST] test_ogata_sylvester_shape")
    E = ogata_sylvester_E([1,1,0.5], [1,2])
    print(f"[DBG] E.shape={E.shape}")
    assert E.shape == (4,4)

def test_dlsim_safe_tuple_handling():
    print("\\n[TEST] test_dlsim_safe_tuple_handling")
    sysd = dlti([1],[1,-0.5], dt=1.0)
    k = np.arange(0,5)
    t, y = dlsim_safe(sysd, np.ones_like(k), t=k)
    print(f"[DBG] t={t}, y={y.squeeze()}")
    assert len(t)==len(y)==5
