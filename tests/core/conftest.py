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
        "registry_uri": "erc1319://0x1457890158DECD360e6d4d979edBcDD59c35feeB:1/owned@1.0.0", # needs new release
        "registry_address": "0x1457890158DECD360e6d4d979edBcDD59c35feeB", # needs new release
    }
