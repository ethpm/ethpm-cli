import json

import pytest

from ethpm_cli.constants import ETHPM_PACKAGES_DIR


@pytest.fixture
def owned_pkg_data(test_assets_dir):
    owned_dir = test_assets_dir / "owned" / "ipfs_uri" / ETHPM_PACKAGES_DIR / "owned"
    owned_raw_manifest = (owned_dir / "manifest.json").read_bytes()
    return {
        "raw_manifest": owned_raw_manifest,
        "manifest": json.loads(owned_raw_manifest),
        "ipfs_uri": "ipfs://QmcxvhkJJVpbxEAa6cgW3B6XwPJb79w9GpNUv2P2THUzZR",
        "content_hash": "QmcxvhkJJVpbxEAa6cgW3B6XwPJb79w9GpNUv2P2THUzZR",
        "registry_uri": "erc1319://0x3F0ED4f69f21ca9d8748c860Ecd0aB6da44BA75a:1/owned@1.0.0",
        "registry_address": "0x3F0ED4f69f21ca9d8748c860Ecd0aB6da44BA75a",
    }
