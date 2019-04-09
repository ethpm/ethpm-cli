from ethpm_cli.manager import Package


def test_package(owned_pkg_data):
    package = Package(owned_pkg_data["ipfs_uri"])

    assert package.alias is None
    assert package.target_uri == owned_pkg_data["ipfs_uri"]
    assert package.manifest_uri == owned_pkg_data["ipfs_uri"]
    assert package.registry_address is None
    assert package.resolved_content_hash == owned_pkg_data["content_hash"]
    assert package.raw_manifest == owned_pkg_data["raw_manifest"]
    assert package.manifest == owned_pkg_data["manifest"]


def test_package_with_alias(owned_pkg_data):
    package = Package(owned_pkg_data["ipfs_uri"], "owned-alias")

    assert package.alias == "owned-alias"
    assert package.target_uri == owned_pkg_data["ipfs_uri"]
    assert package.manifest_uri == owned_pkg_data["ipfs_uri"]
    assert package.registry_address is None
    assert package.resolved_content_hash == owned_pkg_data["content_hash"]
    assert package.raw_manifest == owned_pkg_data["raw_manifest"]
    assert package.manifest == owned_pkg_data["manifest"]


def test_package_with_registry_uri(owned_pkg_data):
    package = Package(owned_pkg_data["registry_uri"])

    assert package.alias is None
    assert package.target_uri == owned_pkg_data["registry_uri"]
    assert package.manifest_uri == owned_pkg_data["ipfs_uri"]
    assert package.registry_address == owned_pkg_data["registry_address"]
    assert package.resolved_content_hash == owned_pkg_data["content_hash"]
    assert package.raw_manifest == owned_pkg_data["raw_manifest"]
    assert package.manifest == owned_pkg_data["manifest"]


def test_package_with_registry_uri_with_alias(owned_pkg_data):
    package = Package(owned_pkg_data["registry_uri"], "owned-alias")

    assert package.alias == "owned-alias"
    assert package.target_uri == owned_pkg_data["registry_uri"]
    assert package.manifest_uri == owned_pkg_data["ipfs_uri"]
    assert package.registry_address == owned_pkg_data["registry_address"]
    assert package.resolved_content_hash == owned_pkg_data["content_hash"]
    assert package.raw_manifest == owned_pkg_data["raw_manifest"]
    assert package.manifest == owned_pkg_data["manifest"]
