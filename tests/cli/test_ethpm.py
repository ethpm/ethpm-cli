import shutil

import pexpect

from ethpm_cli._utils.testing import check_dir_trees_equal


def test_ethpm_list(test_assets_dir):
    ethpm_dir = test_assets_dir / "multiple" / "_ethpm_packages"
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


def test_ethpm_install(tmp_path, test_assets_dir):
    ethpm_dir = tmp_path / "_ethpm_packages"
    ethpm_dir.mkdir()
    child = pexpect.spawn(
        "ethpm install ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW "
        f"--ethpm-dir {ethpm_dir}"
    )
    child.expect("EthPM CLI v0.1.0a0\r\n")
    child.expect("\r\n")
    child.expect(
        "owned package sourced from ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW "
        f"installed to {ethpm_dir}.\r\n"
    )
    assert check_dir_trees_equal(
        ethpm_dir, test_assets_dir / "owned" / "ipfs_uri" / "_ethpm_packages"
    )


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


def test_unsupported_command():
    child = pexpect.spawn("ethpm invalid")
    child.expect("EthPM CLI v0.1.0a0\r\n")
    child.expect("\r\n")
    child.expect(
        "ethpm: error: argument command: invalid choice: 'invalid' "
        r"\(choose from 'scrape', 'install', 'uninstall', 'list'\)\r\n"
    )
