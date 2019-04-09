from pathlib import Path

import pytest

from ethpm_cli.exceptions import InstallError
from ethpm_cli.manager import Manager


def test_install_owned(tmpdir, assets_dir):
    manager = Manager(target_dir=Path(tmpdir))
    manager.install("ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW")

    actual_owned = Path(tmpdir) / "ethpm_packages"
    expected_owned = assets_dir / "owned" / "ipfs_uri" / "ethpm_packages"

    actual_lock = actual_owned / "ethpm.lock"
    expected_lock = expected_owned / "ethpm.lock"

    actual_manifest = actual_owned / "owned" / "manifest.json"
    expected_manifest = expected_owned / "owned" / "manifest.json"

    actual_src = actual_owned / "owned" / "src" / "contracts" / "Owned.sol"
    expected_src = expected_owned / "owned" / "src" / "contracts" / "Owned.sol"

    assert manager.installed_pkgs == ["owned"]
    assert actual_lock.read_text() == expected_lock.read_text().rstrip("\n")
    assert actual_manifest.read_text() == expected_manifest.read_text().rstrip("\n")
    assert actual_src.read_text() == expected_src.read_text().rstrip("\n")


def test_install_owned_with_alias(tmpdir, assets_dir):
    manager = Manager(target_dir=Path(tmpdir))
    manager.install(
        "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW", alias="owned-alias"
    )

    actual_owned = Path(tmpdir) / "ethpm_packages"
    expected_owned = assets_dir / "owned" / "ipfs_uri_alias" / "ethpm_packages"

    actual_lock = actual_owned / "ethpm.lock"
    expected_lock = expected_owned / "ethpm.lock"

    actual_manifest = actual_owned / "owned-alias" / "manifest.json"
    expected_manifest = expected_owned / "owned-alias" / "manifest.json"

    actual_src = actual_owned / "owned-alias" / "src" / "contracts" / "Owned.sol"
    expected_src = expected_owned / "owned-alias" / "src" / "contracts" / "Owned.sol"

    assert manager.installed_pkgs == ["owned"]
    assert actual_lock.read_text() == expected_lock.read_text().rstrip("\n")
    assert actual_manifest.read_text() == expected_manifest.read_text().rstrip("\n")
    assert actual_src.read_text() == expected_src.read_text().rstrip("\n")


def test_install_owned_via_registry_uri(tmpdir, assets_dir):
    manager = Manager(target_dir=Path(tmpdir))
    manager.install(
        "ercXXX://0x6b5DA3cA4286Baa7fBaf64EEEE1834C7d430B729/owned?version=1.0.0"
    )

    actual_owned = Path(tmpdir) / "ethpm_packages"
    expected_owned = assets_dir / "owned" / "registry_uri" / "ethpm_packages"

    actual_lock = actual_owned / "ethpm.lock"
    expected_lock = expected_owned / "ethpm.lock"

    actual_manifest = actual_owned / "owned" / "manifest.json"
    expected_manifest = expected_owned / "owned" / "manifest.json"

    actual_src = actual_owned / "owned" / "src" / "contracts" / "Owned.sol"
    expected_src = expected_owned / "owned" / "src" / "contracts" / "Owned.sol"

    assert manager.installed_pkgs == ["owned"]
    assert actual_lock.read_text() == expected_lock.read_text().rstrip("\n")
    assert actual_manifest.read_text() == expected_manifest.read_text().rstrip("\n")
    assert actual_src.read_text() == expected_src.read_text().rstrip("\n")


def test_manager_defaults_to_cwd(tmpdir, monkeypatch):
    cwd = Path(tmpdir)
    monkeypatch.chdir(cwd)
    manager = Manager()
    assert manager.ethpm_dir == cwd / "ethpm_packages"


def test_manager_accepts_custom_ethpm_dir(tmpdir):
    cwd = Path(tmpdir)
    test_dir = cwd / "test"
    test_dir.mkdir()
    manager = Manager(target_dir=test_dir)
    assert manager.ethpm_dir == test_dir / "ethpm_packages"


def test_manager_rejects_nonexistent_ethpm_dirs():
    with pytest.raises(InstallError):
        Manager(target_dir="/invalid/path")
