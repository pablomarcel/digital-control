import os, sys, logging, pprint
from stateSpace.stateSpaceTool.tools import class_diagram

def test_class_diagram_writes_file(tmp_path, capsys, caplog):
    caplog.set_level(logging.DEBUG, logger="stateSpace.stateSpaceTool.tools.class_diagram")
    outdir = tmp_path / "outdir"

    # Log rich context
    print("=== TEST CONTEXT ===")
    print("cwd:", os.getcwd())
    print("sys.argv:", sys.argv)
    print("env.PYTEST_CURRENT_TEST:", os.environ.get("PYTEST_CURRENT_TEST"))
    print("intended outdir:", outdir)

    # Call with explicit argv to be unambiguous
    class_diagram.main(["--out", str(outdir)])

    # Capture output and logs for debugging visibility
    stdout, stderr = capsys.readouterr()
    print("=== STDOUT ===")
    print(stdout)
    print("=== STDERR ===")
    print(stderr)

    # Ensure file exists
    assert (outdir / "stateSpaceTool_class_diagram.puml").exists()

    # Show collected logs (no assertion on content, just visibility)
    if caplog.records:
        print("=== LOG RECORDS ===")
        for r in caplog.records:
            print(f"{r.levelname} {r.name}: {r.getMessage()}")
