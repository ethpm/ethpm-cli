from argparse import Namespace
import json
from pathlib import Path
import tempfile

import eth_keyfile
import pytest

from ethpm_cli.config import Config
from ethpm_cli.constants import ETHPM_DIR_NAME, KEYFILE_PATH

ASSETS_DIR = Path(__file__).parent / "core" / "assets"


@pytest.fixture
def test_assets_dir():
    return ASSETS_DIR


@pytest.fixture(autouse=True)
def config(tmpdir, monkeypatch):
    monkeypatch.chdir(tmpdir)
    xdg_ethpm_dir = Path(tmpdir / "xdg_ethpmcli_dir")
    monkeypatch.setenv("XDG_ETHPMCLI_ROOT", str(xdg_ethpm_dir))

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
