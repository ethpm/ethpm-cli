from argparse import Namespace
import json
from pathlib import Path
import tempfile

import eth_keyfile
import pytest

from ethpm_cli.config import Config
from ethpm_cli.constants import ETHPM_DIR_NAME

from ethpm_cli._utils.xdg import get_xdg_ethpmcli_root
from ethpm_cli.config import Config
from ethpm_cli.constants import ETHPM_PACKAGES_DIR, KEYFILE_PATH

ASSETS_DIR = Path(__file__).parent / "core" / "assets"


@pytest.fixture
def test_assets_dir():
    return ASSETS_DIR


@pytest.fixture(autouse=True)
def config(tmpdir, monkeypatch):
    monkeypatch.chdir(tmpdir)

    # Create tmp xdg dir and set as env variable
    xdg_ethpm_dir = Path(tmpdir) / "xdg_ethpmcli_dir"
    monkeypatch.setenv("XDG_ETHPMCLI_ROOT", str(xdg_ethpm_dir))

    # Create tmp _ethpm_packages dir
    ethpm_dir = Path(tmpdir) / ETHPM_PACKAGES_DIR
    ethpm_dir.mkdir()

    # Create basic Config
    namespace = Namespace()
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
def keyfile(keyfile_auth):
    private_key, _, password = keyfile_auth
    xdg_ethpm_dir = get_xdg_ethpmcli_root()
    assert "pytest" in str(xdg_ethpm_dir)
    tmp_keyfile = xdg_ethpm_dir / KEYFILE_PATH
    keyfile_json = eth_keyfile.create_keyfile_json(private_key, password)
    tmp_keyfile.write_text(json.dumps(keyfile_json))
    return tmp_keyfile


@pytest.fixture(autouse=True)
def _clean_current_working_directory(monkeypatch):
    with tempfile.TemporaryDirectory() as temp_dir:
        monkeypatch.chdir(temp_dir)
        yield


@pytest.fixture
def owned_pkg_data(test_assets_dir):
    owned_dir = test_assets_dir / "owned" / "ipfs_uri" / ETHPM_PACKAGES_DIR / "owned"
    owned_raw_manifest = (owned_dir / "manifest.json").read_bytes()
    return {
        "raw_manifest": owned_raw_manifest,
        "manifest": json.loads(owned_raw_manifest),
        "ipfs_uri": "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
        "content_hash": "QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
        "registry_uri": "erc1319://0x6b5DA3cA4286Baa7fBaf64EEEE1834C7d430B729:1/owned?version=1.0.0",  # noqa: E501
        "registry_address": "0x6b5DA3cA4286Baa7fBaf64EEEE1834C7d430B729",
    }
