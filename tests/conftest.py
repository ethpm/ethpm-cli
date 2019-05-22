from pathlib import Path

import pytest

ASSETS_DIR = Path(__file__).parent / "core" / "assets"


@pytest.fixture
def test_assets_dir():
    return ASSETS_DIR
