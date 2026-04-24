import pytest
from introduction.vcdTool.apis import RunRequest

def test_validate_ok():
    r = RunRequest(vcd="x.vcd", backend="mpl", units="us", csv_units="s")
    r.validate()  # should not raise

@pytest.mark.parametrize("backend", ["bad", "MPLX"])
def test_validate_bad_backend(backend):
    r = RunRequest(vcd="x.vcd", backend=backend)
    with pytest.raises(ValueError):
        r.validate()

@pytest.mark.parametrize("units", ["msec","seconds","μs"])
def test_validate_bad_units(units):
    r = RunRequest(vcd="x.vcd", units=units)
    with pytest.raises(ValueError):
        r.validate()

@pytest.mark.parametrize("units", ["msec","seconds","μs"])
def test_validate_bad_csv_units(units):
    r = RunRequest(vcd="x.vcd", csv_units=units)
    with pytest.raises(ValueError):
        r.validate()
