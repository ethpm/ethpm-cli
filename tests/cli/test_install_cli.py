import pexpect
import requests

from ethpm_cli._utils.filesystem import check_dir_trees_equal
from ethpm_cli.constants import ETHPM_CLI_VERSION, ETHPM_PACKAGES_DIR


def test_ethpm_install(tmp_path, test_assets_dir):
    ethpm_dir = tmp_path / ETHPM_PACKAGES_DIR
    child = pexpect.spawn(
        "ethpm install ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW "
        f"--ethpm-dir {ethpm_dir}"
    )
    child.expect(
        f"A command line tool for the Ethereum Package Manager. v{ETHPM_CLI_VERSION}\r\n"
    )
    child.expect("\r\n")
    child.expect(
        "owned package sourced from ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW "
        f"installed to {ethpm_dir}.\r\n"
    )
    assert check_dir_trees_equal(
        ethpm_dir, test_assets_dir / "owned" / "ipfs_uri" / ETHPM_PACKAGES_DIR
    )


def test_ethpm_install_from_etherscan(tmp_path, test_assets_dir, monkeypatch):
    class MockSuccessResponse(object):
        def json(self):
            etherscan_response = (
                test_assets_dir / "dai" / "etherscan_response.json"
            ).read_text()
            return {"result": etherscan_response}

    def mock_success_get(url):
        return MockSuccessResponse()

    monkeypatch.setattr(requests, "get", mock_success_get)

    dai_mainnet_addr = "0x89d24A6b4CcB1B6fAA2625fE562bDD9a23260359"
    etherscan_uri = f"etherscan://{dai_mainnet_addr}:1"
    ethpm_dir = tmp_path / ETHPM_PACKAGES_DIR
    child = pexpect.spawn(
        f"ethpm install {etherscan_uri} --package-name dai --package-version 1.0.0 "
        f"--ethpm-dir {ethpm_dir}"
    )
    child.expect(
        f"A command line tool for the Ethereum Package Manager. v{ETHPM_CLI_VERSION}\r\n"
    )
    child.expect("\r\n")
    child.expect(
        f"dai package sourced from {etherscan_uri} installed to {ethpm_dir}.\r\n"
    )
    # cannot check_dir_trees_equal b/c block_uri is always updated to newest value


def test_ethpm_install_etherscan_raises_exception_for_unverified_contract(
    tmp_path, monkeypatch
):
    class MockBadResponse(object):
        def json(self):
            return {"message": "NOTOK"}

    def mock_bad_get(url):
        return MockBadResponse()

    monkeypatch.setattr(requests, "get", mock_bad_get)

    unverified_contract_addr = "0x6b5DA3cA4286Baa7fBaf64EEEE1834C7d430B729"
    ethpm_dir = tmp_path / ETHPM_PACKAGES_DIR
    child = pexpect.spawn(
        f"ethpm install etherscan://{unverified_contract_addr}:1 --package-name dai "
        f"--package-version 1.0.0 --ethpm-dir {ethpm_dir}"
    )
    child.expect(
        f"A command line tool for the Ethereum Package Manager. v{ETHPM_CLI_VERSION}\r\n"
    )
    child.expect("\r\n")
    child.expect(
        f"Contract at {unverified_contract_addr} unavailable or has not "
        "been verified on Etherscan."
    )
