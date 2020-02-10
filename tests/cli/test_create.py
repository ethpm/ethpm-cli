import filecmp

import pexpect

from ethpm_cli.constants import SOLC_INPUT
from ethpm_cli.main import ENTRY_DESCRIPTION


def test_custom_manifest_builder(tmp_project_dir, test_assets_dir):
    child = pexpect.spawn(
        f"ethpm create wizard --project-dir {tmp_project_dir}", timeout=5
    )
    child.expect(ENTRY_DESCRIPTION)
    child.expect("\r\n")
    child.expect("Manifest Wizard")
    child.expect("---------------\r\n")
    child.expect("Create ethPM manifests for local projects.")
    child.expect("\r\n")
    child.expect("Enter your package's name: ")
    child.sendline("ethpm-registry")
    child.expect("Enter your package's version: ")
    child.sendline("2.0.0a1")
    child.expect("Would you like to add a description to your package?")
    child.sendline("y")
    child.expect("Enter your description: ")
    child.sendline("A basic Solidity implementation of ERC1319.")
    child.expect("Would you like to add a license to your package?")
    child.sendline("y")
    child.expect("Enter your license: ")
    child.sendline("MIT")
    child.expect("Would you like to add authors to your package?")
    child.sendline("y")
    child.expect("Enter an author, or multiple authors separated by commas: ")
    child.sendline("Nick Gheorghita")
    child.expect("Would you like to add keywords to your package?")
    child.sendline("y")
    child.expect("Enter a keyword, or multiple keywords separated by commas: ")
    child.sendline("ethpm, erc1319, solidity, ethereum, package registry")
    child.expect(
        "Would you like to add links to the documentation, repo, or website in your package?"
    )
    child.sendline("y")
    child.expect("Enter a link for your documentation")
    child.sendline("https://github.com/ethereum/EIPs/blob/master/EIPS/eip-1319.md")
    child.expect("Enter a link for your repository")
    child.sendline("https://github.com/ethpm/solidity-registry/")
    child.expect("Enter a link for your website")
    child.sendline("www.ethpm.com")
    child.expect("3 contract types available.\r\n")
    child.expect("\r\n")
    child.expect("Ownable\r\n")
    child.expect("  - Ownable.sol\r\n")
    child.expect("PackageRegistry\r\n")
    child.expect("  - Ownable.sol\r\n")
    child.expect("  - PackageRegistry.sol\r\n")
    child.expect("  - PackageRegistryInterface.sol\r\n")
    child.expect("PackageRegistryInterface\r\n")
    child.expect("  - PackageRegistryInterface.sol\r\n")
    child.expect(
        "Would you like to automatically include all available contract types and their sources?"
    )
    child.sendline("y")
    child.expect("Would you like to inline source files?")
    child.sendline("y")
    child.expect("Would you like to add a deployment to your package?")
    child.sendline("n")
    child.expect("Would you like to validate your manifest against the json schema?")
    child.sendline("y")
    child.expect(
        "Building your manifest. This could take a minute if you're pinning assets to IPFS."
    )
    child.expect("Please enter a filename for your manifest.")
    child.sendline("2.0.0a1")
    child.expect(
        f"Manifest successfully created and written to {tmp_project_dir}/2.0.0a1.json"
    )
    assert filecmp.cmp(
        test_assets_dir / "registry" / "2.0.0a1.json", tmp_project_dir / "2.0.0a1.json"
    )


def test_manifest_builder_amend(tmp_project_dir, test_assets_dir):
    child = pexpect.spawn(
        f"ethpm create wizard --manifest-path {tmp_project_dir / 'owned.json'}",
        timeout=5,
    )
    child.expect(ENTRY_DESCRIPTION)
    child.expect("\r\n")
    child.expect("Manifest Wizard")
    child.expect("---------------\r\n")
    child.expect("Amend a local manifest.")
    child.expect("Valid manifest for <Package owned==1.0.0> found at")
    child.expect(
        r"Description found \(Reusable contracts which implement a privileged 'owner' "
        r"model for authorization.\). Would you like to change it?"
    )
    child.sendline("y")
    child.expect("Enter your new description: ")
    child.sendline("Amended description.")
    child.expect(r"License found \(MIT\). Would you like to change it?")
    child.sendline("y")
    child.expect("Enter your new license: ")
    child.sendline("Amended license.")
    child.expect(
        r"Authors found \(\['Piper Merriam <pipermerriam@gmail.com>'\]\). "
        r"Would you like to change them?"
    )
    child.sendline("y")
    child.expect("Enter an author or multiple authors separated by commas: ")
    child.sendline("amended, authors")
    child.expect(
        r"Keywords found \(\['authorization'\]\). Would you like to change them?"
    )
    child.sendline("y")
    child.expect("Enter a keyword or multiple keywords separated by commas: ")
    child.sendline("amended, keywords")
    child.expect("Links found ")
    child.sendline("y")
    child.expect("Enter a new link for your documentation")
    child.sendline("amended.documentation.com")
    child.expect("Enter a new link for your repository")
    child.sendline("")
    child.expect("Enter a new link for your website")
    child.sendline("amended.website.com")
    child.expect("No deployments found, would you like to add one?")
    child.sendline("n")
    child.expect("Would you like to validate your manifest against the json schema?")
    child.sendline("y")
    child.expect("Please enter a filename for your manifest. ")
    child.sendline("owned")
    child.expect("owned.json already exists. Please provide a different filename.")
    child.sendline("owned-amended-test")
    child.expect("Manifest successfully created and written to ")
    assert filecmp.cmp(
        test_assets_dir / "owned" / "1.0.0-amended.json",
        tmp_project_dir / "owned-amended-test.json",
    )


def test_basic_manifest_builder(tmp_project_dir):
    child = pexpect.spawn(
        f"ethpm create basic --project-dir {tmp_project_dir} "
        "--package-name wallet --package-version 1.0.0"
    )
    child.expect(ENTRY_DESCRIPTION)
    child.expect("\r\n")
    child.expect(
        f"Manifest successfully created and written to {tmp_project_dir}/1.0.0.json"
    )


def test_create_solc_input(tmp_project_dir):
    child = pexpect.spawn(f"ethpm create solc-input --project-dir {tmp_project_dir}")
    child.expect(ENTRY_DESCRIPTION)
    child.expect("\r\n")
    child.expect(
        "Solidity compiler input successfully created and "
        f"written to {tmp_project_dir}/{SOLC_INPUT}"
    )


def test_create_manifest_without_precompiled_assets(tmp_owned_dir):
    child = pexpect.spawn(f"ethpm create wizard --project-dir {tmp_owned_dir}")
    child.expect(ENTRY_DESCRIPTION)
    child.expect("\r\n")
    child.expect(f"Compiling contracts found in {tmp_owned_dir}")
    child.expect("1 contracts found:")
    child.expect("- Owned.sol")
    child.expect("No solidity compiler input detected...")
    child.expect("Solidity compiler input successfully created and written to ")
    child.expect("Solidity compiler detected")
    child.expect("Contracts successfully compiled!")
    child.expect("Manifest Wizard")
    child.expect("---------------\r\n")
