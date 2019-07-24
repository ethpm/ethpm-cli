import shutil

import pexpect

from ethpm_cli._utils.filesystem import check_dir_trees_equal
from ethpm_cli.constants import ETHPM_PACKAGES_DIR


def test_ethpm_list(test_assets_dir):
    ethpm_dir = test_assets_dir / "multiple" / ETHPM_PACKAGES_DIR
    child = pexpect.spawn(f"ethpm list --ethpm-dir {ethpm_dir}")
    child.expect("EthPM CLI v0.1.0a0\r\n")
    child.expect("\r\n")
    child.expect(
        r"owned==1.0.0 --- \(ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW\)\r\n"
    )
    child.expect(
        r"wallet==1.0.0 --- \(ipfs://QmRMSm4k37mr2T3A2MGxAj2eAHGR5veibVt1t9Leh5waV1\)\r\n"
    )
    child.expect(
        r"- safe-math-lib==1.0.0 --- \(ipfs://QmWgvM8yXGyHoGWqLFXvareJsoCZVsdrpKNCLMun3RaSJm\)\r\n"
    )
    child.expect(
        r"- owned==1.0.0 --- \(ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW\)\r\n"
    )


def test_ethpm_list_with_aliased_package(test_assets_dir):
    ethpm_dir = test_assets_dir / "owned" / "ipfs_uri_alias" / ETHPM_PACKAGES_DIR
    child = pexpect.spawn(f"ethpm list --ethpm-dir {ethpm_dir}")
    child.expect("EthPM CLI v0.1.0a0\r\n")
    child.expect("\r\n")
    child.expect(
        "owned @ owned-alias==1.0.0 --- "
        r"\(ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW\)\r\n"
    )


def test_ethpm_install(config, test_assets_dir):
    child = pexpect.spawn(
        "ethpm install ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW "
        f"--ethpm-dir {config.ethpm_dir}"
    )
    child.expect("EthPM CLI v0.1.0a0\r\n")
    child.expect("\r\n")
    child.expect(
        "owned package sourced from ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW "
        f"installed to {config.ethpm_dir}.\r\n"
    )
    assert check_dir_trees_equal(
        config.ethpm_dir, test_assets_dir / "owned" / "ipfs_uri" / ETHPM_PACKAGES_DIR
    )


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
    child.expect("EthPM CLI v0.1.0a0\r\n")
    child.expect("\r\n")
    child.expect(
        "ethpm: error: argument command: invalid choice: 'invalid' "
        r"\(choose from 'registry', 'auth', 'scrape', 'install', 'uninstall', 'list'\)\r\n"
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
    child.expect("EthPM CLI v0.1.0a0\r\n")
    child.expect("\r\n")
    child.expect(r"Found owned installed under the alias\(es\): \('owned-alias',\). ")
    child.expect(
        "To uninstall an aliased package, use the alias as the uninstall argument.\r\n"
    )
