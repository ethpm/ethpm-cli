import shutil

import pexpect

from ethpm_cli._utils.testing import check_dir_trees_equal


def test_ethpm_uninstall(tmp_path, test_assets_dir):
    ethpm_dir = tmp_path / "_ethpm_packages"
    shutil.copytree(test_assets_dir / "multiple" / "_ethpm_packages", ethpm_dir)
    assert check_dir_trees_equal(
        ethpm_dir, test_assets_dir / "multiple" / "_ethpm_packages"
    )
    child = pexpect.spawn(f"ethpm uninstall owned --ethpm-dir {ethpm_dir}")
    child.expect(f"owned uninstalled from {ethpm_dir}\r\n")
    assert check_dir_trees_equal(
        ethpm_dir, test_assets_dir / "wallet" / "ipfs_uri" / "_ethpm_packages"
    )


def test_ethpm_uninstall_nonexistent_package(tmp_path):
    ethpm_dir = tmp_path / "_ethpm_packages"
    ethpm_dir.mkdir()
    child = pexpect.spawn(f"ethpm uninstall owned --ethpm-dir {ethpm_dir}")
    child.expect(
        f"No package with the name owned found installed under {ethpm_dir}.\r\n"
    )


def test_ethpm_uninstall_aliased_package(tmp_path, test_assets_dir):
    ethpm_dir = tmp_path / "_ethpm_packages"
    shutil.copytree(
        test_assets_dir / "owned" / "ipfs_uri_alias" / "_ethpm_packages", ethpm_dir
    )
    assert check_dir_trees_equal(
        ethpm_dir, test_assets_dir / "owned" / "ipfs_uri_alias" / "_ethpm_packages"
    )
    child = pexpect.spawn(f"ethpm uninstall owned --ethpm-dir {ethpm_dir}")
    child.expect("EthPM CLI v0.1.0a0\r\n")
    child.expect("\r\n")
    child.expect(r"Found owned installed under the alias\(es\): \('owned-alias',\). ")
    child.expect(
        "To uninstall an aliased package, use the alias as the uninstall argument.\r\n"
    )
