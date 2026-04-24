from __future__ import annotations
import json, os, tempfile
from introduction.zohTool.io import load_u_from_json, load_u_from_csv

def test_load_json_inline_list():
    u = load_u_from_json('[1, 0.5, 2]')
    assert u == [1.0, 0.5, 2.0]

def test_load_json_inline_objects():
    u = load_u_from_json('[{"u":1},{"u":0.5}]')
    assert u == [1.0, 0.5]

def test_load_json_file_vectors(tmp_path):
    path = tmp_path / 'u.json'
    with open(path, 'w') as f:
        json.dump({"vectors":[{"u":1},{"u":2},{"u":3}]}, f)
    u = load_u_from_json(str(path))
    assert u == [1.0, 2.0, 3.0]

def test_load_csv_variants(tmp_path):
    # plain 'u' column
    p1 = tmp_path / 'u.csv'
    with open(p1, 'w') as f:
        f.write('u\n0\n0.5\n1\n')
    u1 = load_u_from_csv(str(p1))
    assert u1 == [0.0, 0.5, 1.0]

    # k,u with gaps
    p2 = tmp_path / 'u_k.csv'
    with open(p2, 'w') as f:
        f.write('k,u\n0,0.1\n2,0.5\n3,0.5\n5,0\n')
    u2 = load_u_from_csv(str(p2))
    # dense from k=0..5, fill missing with 0
    assert u2 == [0.1, 0.0, 0.5, 0.5, 0.0, 0.0]
