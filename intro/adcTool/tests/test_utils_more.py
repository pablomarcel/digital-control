
import os, tempfile, shutil
from intro.adcTool import utils

def test_bin_zero_padded_grouping_and_plain():
    assert utils.bin_zero_padded(3, 5) == "00011"
    assert utils.bin_zero_padded(0xAB, 8, group=4) == "1010_1011"

def test_fmt_code_variants():
    assert utils.fmt_code(15, 8, "dec") == "15"
    assert utils.fmt_code(15, 8, "hex").startswith("0x")
    assert utils.fmt_code(15, 8, "bin").startswith("0b")
    s = utils.fmt_code(15, 8, "all")
    assert "0b" in s and "0x" in s

def test_resolve_paths_and_ensure_dir(tmp_path):
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()
    # create a file in in_dir
    p = in_dir / "data.csv"
    p.write_text("vin\n0.1\n")
    # relative resolves to in_dir
    assert utils.resolve_input_path("data.csv", str(in_dir)) == str(p)
    # absolute path stays absolute
    assert utils.resolve_input_path(str(p), str(in_dir)) == str(p)
    # inline JSON detected
    inline = "[0.1, 0.2]"
    assert utils.resolve_input_path(inline, str(in_dir)) == inline
    # output relative goes under out_dir and the directory is created
    out_rel = utils.resolve_output_path("foo/bar.txt", str(out_dir))
    assert out_rel.startswith(str(out_dir))
    assert os.path.isdir(os.path.dirname(out_rel))
