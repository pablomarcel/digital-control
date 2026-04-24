
from __future__ import annotations
import os
from rst_controllers.rstPlotTool import utils

def test_paths_and_decorator(tmp_path, monkeypatch):
    # Make OUT_DIR point to a temp place for isolation
    monkeypatch.setattr(utils, "OUT_DIR", str(tmp_path))
    os.makedirs(utils.OUT_DIR, exist_ok=True)

    # Decorate a function that just returns the path it was called with
    @utils.with_out_dir
    def echo(path, *args, **kwargs):
        return path, args, kwargs

    # Pass a filename; decorator should remap into OUT_DIR
    p, args, kwargs = echo("figure.png", 1, k=2)
    assert p == os.path.join(utils.OUT_DIR, "figure.png")
    assert args == (1,)
    assert kwargs == dict(k=2)
