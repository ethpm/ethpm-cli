import shutil

import pexpect

from ethpm_cli._utils.filesystem import check_dir_trees_equal
from ethpm_cli.constants import ETHPM_PACKAGES_DIR
from ethpm_cli.main import ENTRY_DESCRIPTION


def test_ethpm_list(test_assets_dir):
    ethpm_dir = test_assets_dir / "multiple" / ETHPM_PACKAGES_DIR
    child = pexpect.spawn(f"ethpm list --ethpm-dir {ethpm_dir}")
    child.expect(ENTRY_DESCRIPTION)
    child.expect("\r\n")
    child.expect("owned")
    child.expect("1.0.0")
    child.expect("ipfs://QmcxvhkJJVpbxEAa6cgW3B6XwPJb79w9GpNUv2P2THUzZR")
    child.expect("wallet")
    child.expect("1.0.0")
    child.expect("ipfs://QmRALeFkttSr6DLmPiNtAqLcMJYXu4BK3SjZGVgW8VASnm")
    child.expect("safe-math-lib")
    child.expect("1.0.0")
    child.expect("ipfs://QmWnPsiS3Xb8GvCDEBFnnKs8Yk4HaAX6rCqJAaQXGbCoPk")


def test_ethpm_list_with_aliased_package(test_assets_dir):
    ethpm_dir = test_assets_dir / "owned" / "ipfs_uri_alias" / ETHPM_PACKAGES_DIR
    child = pexpect.spawn(f"ethpm list --ethpm-dir {ethpm_dir}")
    child.expect(ENTRY_DESCRIPTION)
    child.expect("\r\n")
    child.expect("owned")
    child.expect("owned-alias")
    child.expect("1.0.0")
    child.expect("ipfs://QmcxvhkJJVpbxEAa6cgW3B6XwPJb79w9GpNUv2P2THUzZR")


def test_ethpm_uninstall(config, test_assets_dir):
    test_ethpm_dir = config.ethpm_dir / ETHPM_PACKAGES_DIR
    shutil.copytree(test_assets_dir / "multiple" / ETHPM_PACKAGES_DIR, test_ethpm_dir)
    assert check_dir_trees_equal(
        test_ethpm_dir, test_assets_dir / "multiple" / ETHPM_PACKAGES_DIR
    )
    child = pexpect.spawn(f"ethpm uninstall owned --ethpm-dir {test_ethpm_dir}")
    child.expect(f"owned uninstalled from {test_ethpm_dir}\r\n")
    assert check_dir_trees_equal(
        test_ethpm_dir, test_assets_dir / "wallet" / "ipfs_uri" / ETHPM_PACKAGES_DIR
    )


def test_unsupported_command():
    child = pexpect.spawn("ethpm invalid")
    child.expect(ENTRY_DESCRIPTION)
    child.expect("\r\n")
    child.expect(
        "ethpm: error: argument command: invalid choice: 'invalid' "
        r"\(choose from 'release', 'auth', 'registry', 'create', 'scrape', "
        r"'install', 'update', 'uninstall', 'list', 'cat', 'get', 'activate'\)\r\n"
    )


def test_ethpm_uninstall_nonexistent_package(config):
    child = pexpect.spawn(f"ethpm uninstall owned --ethpm-dir {config.ethpm_dir}")
    child.expect(
        f"No package with the name owned found installed under {config.ethpm_dir}.\r\n"
    )


def test_ethpm_uninstall_aliased_package(config, test_assets_dir):
    test_ethpm_dir = config.ethpm_dir / ETHPM_PACKAGES_DIR
    shutil.copytree(
        test_assets_dir / "owned" / "ipfs_uri_alias" / ETHPM_PACKAGES_DIR,
        test_ethpm_dir,
    )
    assert check_dir_trees_equal(
        test_ethpm_dir,
        test_assets_dir / "owned" / "ipfs_uri_alias" / ETHPM_PACKAGES_DIR,
    )
    child = pexpect.spawn(f"ethpm uninstall owned --ethpm-dir {test_ethpm_dir}")
    child.expect(ENTRY_DESCRIPTION)
    child.expect("\r\n")
    child.expect(r"Found owned installed under the alias\(es\): \('owned-alias',\). ")
    child.expect(
        "To uninstall an aliased package, use the alias as the uninstall argument.\r\n"
    )
