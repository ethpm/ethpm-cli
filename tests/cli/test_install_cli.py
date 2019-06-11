import pexpect
import requests

from ethpm_cli._utils.testing import check_dir_trees_equal


def test_ethpm_install(tmp_path, test_assets_dir):
    ethpm_dir = tmp_path / "_ethpm_packages"
    ethpm_dir.mkdir()
    child = pexpect.spawn(
        "ethpm install --uri ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW "
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


def test_ethpm_install_from_etherscan(tmp_path, test_assets_dir, monkeypatch):
    class MockResponse(object):
        def json(self):
            etherscan_response = (
                test_assets_dir / "dai" / "etherscan_response.json"
            ).read_text()
            return {"result": etherscan_response}

    def mock_get(url):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    dai_mainnet_addr = "0x89d24A6b4CcB1B6fAA2625fE562bDD9a23260359"
    ethpm_dir = tmp_path / "_ethpm_packages"
    ethpm_dir.mkdir()
    child = pexpect.spawn(
        f"ethpm install --etherscan {dai_mainnet_addr} --package-name dai --version 1.0.0 "
        f"--ethpm-dir {ethpm_dir}"
    )
    child.expect("EthPM CLI v0.1.0a0\r\n")
    child.expect("\r\n")
    child.expect(
        f"dai package sourced from Etherscan @ {dai_mainnet_addr} "
        f"installed to {ethpm_dir}.\r\n"
    )
    # cannot check_dir_trees_equal b/c block uri is always updated to newest value


def test_ethpm_install_etherscan_raises_exception_for_unverified_contract(
    tmp_path, monkeypatch
):
    class MockResponse(object):
        def json(self):
            return {"message": "NOTOK"}

    def mock_get(url):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    unverified_contract_addr = "0x6b5DA3cA4286Baa7fBaf64EEEE1834C7d430B729"
    ethpm_dir = tmp_path / "_ethpm_packages"
    ethpm_dir.mkdir()
    child = pexpect.spawn(
        f"ethpm install --etherscan {unverified_contract_addr} --package-name dai --version 1.0.0 "
        f"--ethpm-dir {ethpm_dir}"
    )
    child.expect("EthPM CLI v0.1.0a0\r\n")
    child.expect("\r\n")
    child.expect(
        f"Contract at {unverified_contract_addr} has not been verified on Etherscan."
    )
