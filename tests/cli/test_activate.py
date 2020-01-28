import pexpect

from ethpm_cli.constants import ETHPM_CLI_VERSION


def test_activate_with_uninstalled_package(test_assets_dir):
    ethpm_dir = test_assets_dir / "owned" / "ipfs_uri" / "_ethpm_packages"
    child = pexpect.spawn(f"ethpm activate invalid --ethpm-dir {ethpm_dir}", timeout=15)
    child.expect(f"ethPM CLI v{ETHPM_CLI_VERSION}\r\n")
    child.expect("\r\n")
    child.expect(f"Package: invalid not installed in ethPM dir: {ethpm_dir}")
    child.close()


def test_activate_with_invalid_uri():
    child = pexpect.spawn(f"ethpm activate http://www.google.com", timeout=15)
    child.expect(f"ethPM CLI v{ETHPM_CLI_VERSION}\r\n")
    child.expect("\r\n")
    child.expect(
        f"http://www.google.com is not a supported URI. The only URIs currently supported "
        "are Registry, Github Blob, Etherscan and IPFS"
    )
    child.close()


def test_activate_locally_installed_pkg_without_contract_types(test_assets_dir):
    child = pexpect.spawn(
        "ethpm activate owned --ethpm-dir "
        f"{test_assets_dir / 'owned' / 'ipfs_uri' / '_ethpm_packages'}",
        timeout=15,
    )
    child.expect(f"ethPM CLI v{ETHPM_CLI_VERSION}\r\n")
    child.expect("\r\n")
    child.expect("Activating package: owned")
    child.expect("No contract types found.")
    child.expect("No deployments found.")
    child.close()


def test_activate_with_aliased_locally_installed_pkg(test_assets_dir):
    child = pexpect.spawn(
        "ethpm activate owned-alias --ethpm-dir "
        f"{test_assets_dir / 'owned' / 'ipfs_uri_alias' / '_ethpm_packages'}",
        timeout=15,
    )
    child.expect(f"ethPM CLI v{ETHPM_CLI_VERSION}\r\n")
    child.expect("\r\n")
    child.expect("Activating package: owned")
    child.expect("No contract types found.")
    child.expect("No deployments found.")
    child.close()


def test_activate_etherscan_uri_with_single_deployment():
    child = pexpect.spawn(
        f"ethpm activate etherscan://0x89d24A6b4CcB1B6fAA2625fE562bDD9a23260359:1",
        timeout=30,
    )
    child.expect(f"ethPM CLI v{ETHPM_CLI_VERSION}\r\n")
    child.expect("\r\n")
    child.expect("Activating package: etherscan")
    child.expect("Found 1 contract types.")
    child.expect(
        "Insufficient assets to generate factory for DSToken. Package must contain "
        "the abi & deployment bytecode to be able to generate a factory."
    )
    child.expect("Found deployments...")
    child.expect("Available deployments:")
    child.expect("- mainnet_DSToken")
    child.expect("Starting IPython console...")
    # test deployment is available
    child.sendline("mainnet_DSToken")
    child.expect("web3._utils.datatypes.LinkableContract at")
    child.close()


def test_activate_ipfs_uri_with_factories_and_deployments():
    child = pexpect.spawn(
        f"ethpm activate ipfs://Qmf5uJd3yChPwxYxHqR1KN2CdXt2pfsAfPzQe8gkNutwT3",
        timeout=30,
    )
    child.expect(f"ethPM CLI v{ETHPM_CLI_VERSION}\r\n")
    child.expect("\r\n")
    child.expect("Activating package: ethregistrar")
    child.expect("Found 29 contract types.")
    child.expect("Found deployments...")
    child.expect("Available contract factories:")
    child.expect("- Address_factory")
    child.expect("- BaseRegistrar_factory")
    child.expect("Available deployments:")
    child.expect("- mainnet_BaseRegistrarImplementation")
    child.expect("Starting IPython console...")
    # test contract factory is available
    child.sendline("Address_factory")
    child.expect("web3._utils.datatypes.LinkableContract")
    # test deployment is available
    child.sendline("mainnet_BaseRegistrarImplementation")
    child.expect("web3._utils.datatypes.LinkableContract at")
    child.close()


def test_activate_github_uri_with_insufficient_contract_types_and_deployments():
    child = pexpect.spawn(
        "ethpm activate https://api.github.com/repos/"
        "ethpm/ethpm-cli/git/blobs/9fb9a7ec579932d251967c3c6b57f543c1909788",
        timeout=30,
    )
    child.expect(f"ethPM CLI v{ETHPM_CLI_VERSION}\r\n")
    child.expect("\r\n")
    child.expect("Activating package: dai")
    child.expect("Found 1 contract types.")
    child.expect(
        "Insufficient assets to generate factory for DSToken. Package must contain "
        "the abi & deployment bytecode to be able to generate a factory."
    )
    child.expect("Found deployments...")
    child.expect("Available deployments:")
    child.expect("- mainnet_DSToken")
    child.expect("Starting IPython console...")
    # test deployment is available
    child.sendline("mainnet_DSToken")
    child.expect("web3._utils.datatypes.LinkableContract at")
    child.close()


def test_activate_registry_uri_with_contract_types_no_deployments():
    child = pexpect.spawn(
        f"ethpm activate erc1319://ens.snakecharmers.eth:1/ens?version=1.0.0",
        timeout=30,
    )
    child.expect(f"ethPM CLI v{ETHPM_CLI_VERSION}\r\n")
    child.expect("\r\n")
    child.expect("Activating package: ens")
    child.expect("Found 10 contract types.")
    child.expect("No deployments found.")
    child.expect("Available contract factories:")
    child.expect("- Deed_factory")
    child.expect("- DeedImplementation_factory")
    child.expect("Starting IPython console...")
    # test contract factory is available
    child.sendline("Deed_factory")
    child.expect("web3._utils.datatypes.LinkableContract")
    child.close()
