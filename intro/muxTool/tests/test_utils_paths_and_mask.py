
import os, tempfile, pathlib
from intro.muxTool.utils import ensure_dir, looks_inline_json, resolve_input_path, resolve_output_path, mask, log_call

def test_looks_inline_json():
    assert looks_inline_json('[{"a":1}]')
    assert looks_inline_json('{"vectors": []}')
    assert not looks_inline_json(" not json ")

def test_ensure_dir_and_resolve_output_path(tmp_path):
    rel = "foo/bar/baz.txt"
    outp = resolve_output_path(rel, str(tmp_path))
    assert str(tmp_path) in outp
    assert os.path.exists(os.path.dirname(outp))

    abs_target = os.path.join(str(tmp_path), "abs", "file.txt")
    outp2 = resolve_output_path(abs_target, "ignored")
    assert outp2 == abs_target and os.path.exists(os.path.dirname(outp2))

def test_resolve_input_path(tmp_path):
    f = tmp_path / "data.json"
    f.write_text('[{"sel":0,"d0":1,"d1":2,"d2":3,"d3":4}]')
    # absolute path stays as-is
    assert resolve_input_path(str(f), "in") == str(f)
    # relative under in_dir is found
    in_dir = tmp_path / "inputs"
    in_dir.mkdir()
    (in_dir / "v.json").write_text('[{"sel":1,"d0":5,"d1":6,"d2":7,"d3":8}]')
    assert resolve_input_path("v.json", str(in_dir)).endswith("v.json")
    # inline stays inline
    inline = '[{"sel":2,"d0":9,"d1":10,"d2":11,"d3":12}]'
    assert resolve_input_path(inline, "ignored") == inline

def test_mask_and_log_decorator(capsys):
    @log_call
    def f(x): 
        return mask(x, 3)  # 3 bits
    val = f(0b1111)
    captured = capsys.readouterr().out
    assert val == 0b111
    assert "[log] -> f" in captured and "[log] <- f" in captured
