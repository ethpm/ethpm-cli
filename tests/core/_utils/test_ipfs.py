import json
from ethpm_cli._utils.ipfs import pin_local_manifest


def test_pin_local_manifest(test_assets_dir):
    local_manifest_path = test_assets_dir / "owned" / "1.0.0.json"
    expected_manifest = json.loads(
        local_manifest_path.read_text()
    )
    (package_name, package_version, manifest_uri) = pin_local_manifest(local_manifest_path)
    assert package_name == expected_manifest["package_name"]
    assert package_version == expected_manifest["version"]
    assert manifest_uri == "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW"
