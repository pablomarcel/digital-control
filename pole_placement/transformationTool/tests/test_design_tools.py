
from __future__ import annotations
import os, tempfile, numpy as np

from pole_placement.transformationTool.design import print_header, show_matrix_block, export_bundle
from pole_placement.transformationTool.tools.class_diagram import main as classdiag_main

def test_design_helpers_and_export(tmp_path, monkeypatch):
    # redirect out dir by monkeypatching utils
    from pole_placement.transformationTool import utils
    monkeypatch.setattr(utils, "OUTDIR", str(tmp_path))
    utils.ensure_outdir()

    print_header("Demo")
    show_matrix_block(np.eye(2), np.ones((2,1)), np.ones((1,2)), np.zeros((1,1)), True)
    export_bundle("demo_export", np.eye(2), np.eye(2), np.ones((2,1)), np.ones((1,2)), np.zeros((1,1)), True, True)

    # files created
    assert (tmp_path / "demo_export.json").exists()
    assert (tmp_path / "demo_export_T.csv").exists()
    assert (tmp_path / "demo_export_Ahat.csv").exists()

def test_tools_class_diagram(tmp_path):
    classdiag_main(str(tmp_path))
    assert (tmp_path / "transformationTool_class_diagram.puml").exists()
