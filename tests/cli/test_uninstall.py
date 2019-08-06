from distutils.dir_util import copy_tree

import pexpect

from ethpm_cli._utils.filesystem import check_dir_trees_equal
from ethpm_cli.constants import ETHPM_CLI_VERSION, ETHPM_PACKAGES_DIR


def test_ethpm_uninstall(tmp_path, test_assets_dir):
    ethpm_dir = tmp_path / ETHPM_PACKAGES_DIR
    copy_tree(str(test_assets_dir / "multiple" / ETHPM_PACKAGES_DIR), str(ethpm_dir))
    assert check_dir_trees_equal(
        ethpm_dir, test_assets_dir / "multiple" / ETHPM_PACKAGES_DIR
    )
    child = pexpect.spawn(f"ethpm uninstall owned --ethpm-dir {ethpm_dir}")
    child.expect(f"owned uninstalled from {ethpm_dir}\r\n")
    assert check_dir_trees_equal(
        ethpm_dir, test_assets_dir / "wallet" / "ipfs_uri" / ETHPM_PACKAGES_DIR
    )


def test_ethpm_uninstall_nonexistent_package(tmp_path):
    ethpm_dir = tmp_path / ETHPM_PACKAGES_DIR
    child = pexpect.spawn(f"ethpm uninstall owned --ethpm-dir {ethpm_dir}")
    child.expect(
        f"No package with the name owned found installed under {ethpm_dir}.\r\n"
    )


def test_ethpm_uninstall_aliased_package(tmp_path, test_assets_dir):
    ethpm_dir = tmp_path / ETHPM_PACKAGES_DIR
    copy_tree(
        str(test_assets_dir / "owned" / "ipfs_uri_alias" / ETHPM_PACKAGES_DIR),
        str(ethpm_dir),
    )
    assert check_dir_trees_equal(
        ethpm_dir, test_assets_dir / "owned" / "ipfs_uri_alias" / ETHPM_PACKAGES_DIR
    )
    child = pexpect.spawn(f"ethpm uninstall owned --ethpm-dir {ethpm_dir}")
    child.expect(f"ethPM CLI v{ETHPM_CLI_VERSION}\r\n")
    child.expect("\r\n")
    child.expect(r"Found owned installed under the alias\(es\): \('owned-alias',\). ")
    child.expect(
        "To uninstall an aliased package, use the alias as the uninstall argument.\r\n"
    )
