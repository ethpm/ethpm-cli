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


@pytest.fixture
def keyfile_auth():
    private_key = b"\x01" * 32
    address = "0x1a642f0E3c3aF545E7AcBD38b07251B3990914F1"
    password = b"password"
    return private_key, address, password


@pytest.fixture
def keyfile(monkeypatch, tmpdir, keyfile_auth):
    private_key, _, password = keyfile_auth
    monkeypatch.chdir(tmpdir)
    ethpmcli_dir = Path(tmpdir / "ethpmcli_dir")
    ethpmcli_dir.mkdir()
    monkeypatch.setenv("XDG_ETHPMCLI_ROOT", str(ethpmcli_dir))
    tmp_keyfile = ethpmcli_dir / KEYFILE_PATH
    tmp_keyfile.touch()
    keyfile_json = eth_keyfile.create_keyfile_json(private_key, password)
    tmp_keyfile.write_text(json.dumps(keyfile_json))
    return tmp_keyfile


@pytest.fixture(autouse=True)
def _clean_current_working_directory(monkeypatch):
    with tempfile.TemporaryDirectory() as temp_dir:
        monkeypatch.chdir(temp_dir)
        yield
