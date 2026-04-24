
import sympy as sp
from state_space.stateSolverTool.core import leverrier_faddeev, inverse_zI_minus_G, example_system

def test_leverrier_matches_charpoly():
    G, H, C, D, x0, u = example_system("ogata_5_2")
    a, Hs = leverrier_faddeev(G)
    z = sp.symbols('z')
    # Construct polynomial from a-list
    det_via_a = z**G.rows
    for i, ai in enumerate(a, start=1):
        det_via_a += ai * z**(G.rows - i)
    det_direct = sp.factor((z*sp.eye(G.rows) - G).det())
    assert sp.simplify(det_via_a - det_direct) == 0

def test_inverse_zI_minus_G_shapes():
    G, *_ = example_system("ogata_5_2")
    z = sp.symbols('z')
    inv, det, adj, a, H = inverse_zI_minus_G(G, z)
    assert inv.shape == G.shape
    assert adj.shape == G.shape
    assert det.is_polynomial(z)
