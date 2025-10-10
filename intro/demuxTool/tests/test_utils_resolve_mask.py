from __future__ import annotations
import os
from intro.demuxTool.utils import resolve_input_path, resolve_output_path, mask

def test_resolve_input_path_file_and_inline(tmp_path):
    in_dir = tmp_path / "in"; in_dir.mkdir()
    jfile = in_dir / "v.json"
    jfile.write_text('[{"sel":0,"x":1}]', encoding="utf-8")
    # relative -> in_dir file
    p = resolve_input_path("v.json", str(in_dir))
    assert os.path.exists(p)
    # inline passthrough
    inline = '[{"sel":1,"x":3}]'
    assert resolve_input_path(inline, str(in_dir)) == inline
    # absolute path passthrough
    assert resolve_input_path(str(jfile), str(in_dir)) == str(jfile)

def test_resolve_output_path_and_mask(tmp_path):
    out_dir = tmp_path / "out"
    outp = resolve_output_path("r.csv", str(out_dir))
    # should be under out_dir
    assert outp.startswith(str(out_dir))
    # ensure directory created
    assert os.path.isdir(str(out_dir))
    # absolute passthrough
    absfile = tmp_path / "abs.csv"
    p2 = resolve_output_path(str(absfile), str(out_dir))
    assert p2 == str(absfile)
    # mask behaviour
    assert mask(0b111, 2) == 0b11
    assert mask(0x3F, 4) == 0xF
