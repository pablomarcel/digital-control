import logging
import pytest

def pytest_configure(config):
    # Default console logging for tests; can be overridden via CLI flags
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s %(name)s:%(lineno)d | %(message)s"
    )
