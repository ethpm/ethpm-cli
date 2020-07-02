import json

from ethpm import get_ethpm_spec_dir

from ethpm_cli._utils.ipfs import pin_local_manifest


def test_pin_local_manifest(test_assets_dir):
    ethpm_spec_dir = get_ethpm_spec_dir()
    local_manifest_path = ethpm_spec_dir / "examples" / "owned" / "v3.json"
    expected_manifest = json.loads(local_manifest_path.read_text())
    (package_name, package_version, manifest_uri) = pin_local_manifest(
        local_manifest_path
    )
    assert package_name == expected_manifest["name"]
    assert package_version == expected_manifest["version"]
    assert manifest_uri == "ipfs://QmcxvhkJJVpbxEAa6cgW3B6XwPJb79w9GpNUv2P2THUzZR"
