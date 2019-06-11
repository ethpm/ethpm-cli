import pexpect


def test_verify_mainnet_dai(test_assets_dir):
    dai_mainnet_addr = '0x89d24A6b4CcB1B6fAA2625fE562bDD9a23260359'
    ethpm_dir = test_assets_dir / 'dai' / '_ethpm_packages'
    child = pexpect.spawn(f"ethpm verify dai:DSToken --address {dai_mainnet_addr} --ethpm-dir {ethpm_dir}")
    child.expect("EthPM CLI v0.1.0a0\r\n")
    child.expect("\r\n")
    child.expect(f"Valid: Contract code found at {dai_mainnet_addr} matches contract type: DSToken located in the dai package.")


def test_verify_with_incorrect_match(test_assets_dir):
    incorrect_contract_addr = '0x2eb1E8FD394222df25638CfA8f0e5e7998A9dc1f'
    ethpm_dir = test_assets_dir / 'dai' / '_ethpm_packages'
    child = pexpect.spawn(f"ethpm verify dai:DSToken --address {incorrect_contract_addr} --ethpm-dir {ethpm_dir}")
    child.expect("EthPM CLI v0.1.0a0\r\n")
    child.expect("\r\n")
    child.expect(f"Invalid: Contract code found at {incorrect_contract_addr} does not match the contract type: DSToken located in the dai package.")


def test_verify_with_uninstalled_package_raises_exception(test_assets_dir):
    dai_mainnet_addr = '0x89d24A6b4CcB1B6fAA2625fE562bDD9a23260359'
    ethpm_dir = test_assets_dir / 'dai' / '_ethpm_packages'
    child = pexpect.spawn(f"ethpm verify xdai:DSToken --address {dai_mainnet_addr} --ethpm-dir {ethpm_dir}")
    child.expect("EthPM CLI v0.1.0a0\r\n")
    child.expect("\r\n")
    child.expect("InstallError: xdai is not installed.")


def test_verify_with_unavailable_contract_type_raises_exception(test_assets_dir):
    dai_mainnet_addr = '0x89d24A6b4CcB1B6fAA2625fE562bDD9a23260359'
    ethpm_dir = test_assets_dir / 'dai' / '_ethpm_packages'
    child = pexpect.spawn(f"ethpm verify dai:xDSToken --address {dai_mainnet_addr} --ethpm-dir {ethpm_dir}")
    child.expect("EthPM CLI v0.1.0a0\r\n")
    child.expect("\r\n")
    child.expect(r"InstallError: xDSToken not available in dai package. Available contract types include: \['DSToken'\].")
