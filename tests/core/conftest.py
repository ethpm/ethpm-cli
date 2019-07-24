from argparse import Namespace
import json
from pathlib import Path

import pytest

from ethpm_cli.config import Config
from ethpm_cli.constants import ETHPM_DIR_NAME


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
def owned_pkg_data(test_assets_dir):
    owned_dir = test_assets_dir / "owned" / "ipfs_uri" / ETHPM_DIR_NAME / "owned"
    owned_raw_manifest = (owned_dir / "manifest.json").read_bytes()
    return {
        "raw_manifest": owned_raw_manifest,
        "manifest": json.loads(owned_raw_manifest),
        "ipfs_uri": "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
        "content_hash": "QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
        "registry_uri": "erc1319://0x6b5DA3cA4286Baa7fBaf64EEEE1834C7d430B729:1/owned?version=1.0.0",  # noqa: E501
        "registry_address": "0x6b5DA3cA4286Baa7fBaf64EEEE1834C7d430B729",
    }
