from __future__ import annotations

import os
import shutil
import sys
import tempfile

import pytest

scripts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from generate_synthetic_data import generate_dataset  # noqa: E402


@pytest.fixture(scope="session")
def synthetic_dataset() -> str:
    temp_dir = tempfile.mkdtemp(prefix="radscan_test_")
    generate_dataset(temp_dir)
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_output_dir() -> str:
    temp_dir = tempfile.mkdtemp(prefix="radscan_test_out_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)
