"""Pytest configuration for easyeda2kicad tests."""

import shutil
import tempfile
from pathlib import Path

import pytest


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--create-reference",
        action="store_true",
        default=False,
        help="Create reference files instead of comparing"
    )


@pytest.fixture
def create_reference(request):
    """Check if we should create reference files."""
    return request.config.getoption("--create-reference")


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp(prefix="easyeda2kicad_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def reference_dir():
    """Get or create reference directory for baseline files."""
    ref_dir = Path(__file__).parent / "reference_outputs"
    ref_dir.mkdir(exist_ok=True)
    return ref_dir
