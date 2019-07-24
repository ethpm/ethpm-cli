from argparse import Namespace
from pathlib import Path
import tempfile

import pytest

from ethpm_cli.config import Config
from ethpm_cli.constants import ETHPM_DIR_NAME

ASSETS_DIR = Path(__file__).parent / "core" / "assets"


@pytest.fixture
def test_assets_dir():
    return ASSETS_DIR


@pytest.fixture
def config(tmpdir):
    namespace = Namespace()
    ethpm_dir = Path(tmpdir) / ETHPM_DIR_NAME
    ethpm_dir.mkdir()
    namespace.local_ipfs = False
    namespace.install_uri = None
    namespace.alias = None
    namespace.ethpm_dir = ethpm_dir
    return Config(namespace)


@pytest.fixture(autouse=True)
def _clean_current_working_directory(monkeypatch):
    with tempfile.TemporaryDirectory() as temp_dir:
        monkeypatch.chdir(temp_dir)
        yield
