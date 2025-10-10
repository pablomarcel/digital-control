from __future__ import annotations
import os, tempfile
from intro.zohTool.utils import ensure_dir, looks_inline_json, resolve_input_path, resolve_output_path

def test_looks_inline_json_variants():
    assert looks_inline_json("[1,2]")
    assert looks_inline_json("{\"a\":1}")
    assert not looks_inline_json("foo.json")

def test_resolve_input_path_inline_and_abs(tmp_path):
    # inline
    assert resolve_input_path("[1]", "in") == "[1]"
    # abs file
    p = tmp_path / "u.csv"
    p.write_text("u\n1\n")
    assert resolve_input_path(str(p), "in") == str(p)

def test_resolve_input_path_relative_found(tmp_path):
    in_dir = tmp_path / "in"
    in_dir.mkdir()
    p = in_dir / "u.csv"
    p.write_text("u\n1\n")
    got = resolve_input_path("u.csv", str(in_dir))
    assert got == str(p)

def test_resolve_output_path_rel_and_abs(tmp_path):
    out_dir = tmp_path / "out"
    # relative (should create under out_dir)
    rel = resolve_output_path("a/b/c.out", str(out_dir))
    assert rel.endswith("a/b/c.out")
    assert os.path.exists(os.path.dirname(rel))
    # absolute
    abs_p = tmp_path / "x" / "y.out"
    got = resolve_output_path(str(abs_p), str(out_dir))
    assert got == str(abs_p)
    assert os.path.exists(abs_p.parent)
