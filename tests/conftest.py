"""Shared test configuration and fixtures."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def temp_dir():
    """Provide a temporary directory for the test session."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
