from pathlib import Path
import tempfile

import pytest

ASSETS_DIR = Path(__file__).parent / "core" / "assets"


@pytest.fixture
def test_assets_dir():
    return ASSETS_DIR


@pytest.fixture(autouse=True)
def _clean_current_working_directory(monkeypatch):
    with tempfile.TemporaryDirectory() as temp_dir:
        monkeypatch.chdir(temp_dir)
        yield
