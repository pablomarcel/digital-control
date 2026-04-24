
from __future__ import annotations
from introduction.dacTool import utils
from introduction.dacTool.apis import RunResult

def test_resolve_paths_and_timecall(tmp_path):
    in_dir = tmp_path / "in"; out_dir = tmp_path / "out"
    in_dir.mkdir(); out_dir.mkdir()
    # relative in -> resolved under in_dir if exists
    f = in_dir / "codes.csv"; f.write_text("code\n0\n")
    assert utils.resolve_input_path("codes.csv", str(in_dir)) == str(f)
    # relative out -> resolved under out_dir
    outp = utils.resolve_output_path("res.csv", str(out_dir))
    assert outp == str(out_dir / "res.csv")

    @utils.timecall
    def fake_run():
        from introduction.dacTool.apis import Row, Update
        return RunResult(rows=[Row(meta={})], updates=[Update(code=0, vo_ideal=0.0, vo_nonideal=0.0)], messages=[])

    res = fake_run()
    assert any("fake_run took" in m for m in res.messages)
