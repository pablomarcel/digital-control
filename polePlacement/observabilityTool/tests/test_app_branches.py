import logging

from polePlacement.observabilityTool.app import ObservabilityApp
from polePlacement.observabilityTool.apis import RunRequest
from polePlacement.observabilityTool.utils import pkg_outdir
import pathlib, json

def test_app_pretty_pbh_gram_finite_minreal_and_saves(tmp_path):
    app = ObservabilityApp()
    # CT stable, observable system; exercise pretty, PBH, Gram, finite-ct, minreal, saves
    req = RunRequest(
        A="-1 0; 0 -2", C="1 0", discrete=False,
        pretty=True, do_pbh=True, do_gram=True, finite_ct=2.0,
        do_minreal=True, save_csv=True, save_gram=True, save_json=True,
        name="ct_full_path", report=str(pathlib.Path(pkg_outdir())/"ct_full_report.txt")
    )
    logger = logging.getLogger('polePlacement.observabilityTool.tests')
    logger.info('Running ct_full_path scenario (should be NOT observable)')
    res = app.run(req)
    logger.info('Got exit code %s', res.exit_code)
    assert res.exit_code == 2
    outdir = pathlib.Path(pkg_outdir())
    # Check a few outputs exist
    assert (outdir/"ct_full_path_obsv.csv").exists()
    assert (outdir/"ct_full_path_gram_inf.csv").exists()
    assert (outdir/"ct_full_path_summary.json").exists()
    assert (outdir/"ct_full_report.txt").exists()
    # Validate summary JSON parses
    data = json.loads((outdir/"ct_full_path_summary.json").read_text())
    assert data["full_obsv_rank_n"] is False
