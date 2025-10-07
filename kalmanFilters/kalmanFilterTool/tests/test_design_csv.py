
import numpy as np, pathlib
from kalmanFilters.kalmanFilterTool.design import CSVExporter

def test_csv_exporter_header_and_rows(tmp_path):
    t = np.linspace(0, 0.1, 4)
    Y = np.vstack([np.arange(4)]).astype(float)  # p=1
    X_true = np.vstack([np.arange(4), np.arange(4)*2.0])
    X_hat  = X_true + 0.1
    path = CSVExporter(out_dir=str(tmp_path)).write(t, Y, X_true, X_hat, "test.csv")
    p = pathlib.Path(path)
    assert p.exists()
    lines = p.read_text().strip().splitlines()
    assert lines[0].startswith("t,y1,x1_true,x2_true,x1_hat,x2_hat")
    assert len(lines) == 5  # header + 4 rows
