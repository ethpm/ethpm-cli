import pexpect

from ethpm_cli.main import ENTRY_DESCRIPTION


def test_activate_with_uninstalled_package(test_assets_dir):
    ethpm_dir = test_assets_dir / "owned" / "ipfs_uri" / "_ethpm_packages"
    child = pexpect.spawn(f"ethpm activate invalid --ethpm-dir {ethpm_dir}", timeout=15)
    child.expect(ENTRY_DESCRIPTION)
    child.expect("\r\n")
    child.expect(f"Package: invalid not installed in ethPM dir: {ethpm_dir}")
    child.close()


def test_activate_with_invalid_uri():
    child = pexpect.spawn("ethpm activate http://www.google.com", timeout=15)
    child.expect(ENTRY_DESCRIPTION)
    child.expect("\r\n")
    child.expect(
        "http://www.google.com is not a supported URI. The only URIs currently supported "
        "are Registry, Github Blob, Etherscan and IPFS"
    )
    child.close()


def test_activate_locally_installed_pkg_without_contract_types(test_assets_dir):
    child = pexpect.spawn(
        "ethpm activate owned --ethpm-dir "
        f"{test_assets_dir / 'owned' / 'ipfs_uri' / '_ethpm_packages'}",
        timeout=15,
    )
    child.expect(ENTRY_DESCRIPTION)
    child.expect("\r\n")
    child.expect("Activating package")
    child.expect("owned")
    child.expect("1.0.0")
    child.expect("No detected contract types.")
    child.expect("No detected deployments.")
    child.close()


def test_activate_with_aliased_locally_installed_pkg(test_assets_dir):
    child = pexpect.spawn(
        "ethpm activate owned-alias --ethpm-dir "
        f"{test_assets_dir / 'owned' / 'ipfs_uri_alias' / '_ethpm_packages'}",
        timeout=15,
    )
    child.expect(ENTRY_DESCRIPTION)
    child.expect("\r\n")
    child.expect("Activating package")
    child.expect("owned")
    child.expect("1.0.0")
    child.expect("No detected contract types.")
    child.expect("No detected deployments.")
    child.close()


def test_activate_etherscan_uri_with_single_deployment():
    child = pexpect.spawn(
        "ethpm activate etherscan://0x89d24A6b4CcB1B6fAA2625fE562bDD9a23260359:1",
        timeout=30,
    )
    child.expect(ENTRY_DESCRIPTION)
    child.expect("\r\n")
    child.expect("Activating package")
    child.expect("etherscan")
    child.expect("1.0.0")
    child.expect("Insufficient assets to generate factory for DSToken")
    child.expect(
        "Successfully generated 1 contract instance from 1 detected deployment."
    )
    child.expect("mainnet_DSToken")
    child.expect("Available Web3 Instances")
    child.expect(
        "Contract instances and web3 instances have not been configured with an account."
    )
    child.expect(
        "The API for web3.py contract factories and instances can be found here:"
    )
    child.expect("Starting IPython console...")
    # test deployment is available
    child.sendline("mainnet_DSToken")
    child.expect("web3._utils.datatypes.LinkableContract at")
    # test w3 is available
    child.sendline("mainnet_w3")
    child.expect("web3.main.Web3 at")
    child.close()


def test_activate_ipfs_uri_with_factories_and_deployments():
    child = pexpect.spawn(
        "ethpm activate ipfs://QmYraovUprvG69Ti8budkvTMq1avdZ8CaGPeVX3Z6JUE7K",
        timeout=30,
    )
    child.expect(ENTRY_DESCRIPTION)
    child.expect("\r\n")
    child.expect("Activating package")
    child.expect("ethregistrar")
    child.expect("3.0.0")
    child.expect(
        "Successfully generated 31 contract factories on mainnet from 31 detected contract types."
    )
    child.expect("Address_factory")
    child.expect("BaseRegistrar_factory")
    child.expect("To get a contract factory on a different chain,")
    child.expect(
        "Successfully generated 1 contract instance from 1 detected deployment."
    )
    child.expect("mainnet_BaseRegistrarImplementation")
    child.expect("Available Web3 Instances")
    child.expect(
        "Contract instances and web3 instances have not been configured with an account."
    )
    child.expect(
        "The API for web3.py contract factories and instances can be found here:"
    )
    child.expect("Starting IPython console...")
    # test contract factory is available
    child.sendline("Address_factory")
    child.expect("web3._utils.datatypes.LinkableContract")
    child.close()


def test_activate_github_uri_with_insufficient_contract_types_and_deployments():
    child = pexpect.spawn(
        "ethpm activate https://api.github.com/repos/"
        "ethpm/ethpm-cli/git/blobs/282c2e293836c9c58ab72b97ac5f9a44a4caf029",
        timeout=30,
    )
    child.expect(ENTRY_DESCRIPTION)
    child.expect("\r\n")
    child.expect("Activating package")
    child.expect("dai")
    child.expect("1.0.0")
    child.expect("Insufficient assets to generate factory for DSToken.")
    child.expect(
        "Successfully generated 1 contract instance from 1 detected deployment."
    )
    child.expect("mainnet_DSToken")
    child.expect("Available Web3 Instances")
    child.expect(
        "Contract instances and web3 instances have not been configured with an account."
    )
    child.expect(
        "The API for web3.py contract factories and instances can be found here:"
    )
    child.expect("Starting IPython console...")
    # test deployment is available
    child.sendline("mainnet_DSToken")
    child.expect("web3._utils.datatypes.LinkableContract at")
    child.close()


def test_activate_registry_uri_with_contract_types_no_deployments():
    child = pexpect.spawn(
        "ethpm activate erc1319://0x3F0ED4f69f21ca9d8748c860Ecd0aB6da44BA75a:1/ens@1.0.0",
        timeout=30,
    )
    child.expect(ENTRY_DESCRIPTION)
    child.expect("\r\n")
    child.expect("Activating package")
    child.expect("ens")
    child.expect("1.0.0")
    child.expect(
        "Successfully generated 10 contract factories on mainnet from 10 detected contract types."
    )
    child.expect("Deed_factory")
    child.expect("DeedImplementation_factory")
    child.expect("To get a contract factory on a different chain,")
    child.expect("No detected deployments.")
    child.expect("Available Web3 Instances")
    child.expect("Starting IPython console...")
    # test contract factory is available
    child.sendline("Deed_factory")
    child.expect("web3._utils.datatypes.LinkableContract")
    child.close()
