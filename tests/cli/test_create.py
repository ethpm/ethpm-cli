import filecmp

from ethpm import ASSETS_DIR
import pexpect

from ethpm_cli.constants import ETHPM_CLI_VERSION, SOLC_INPUT


def test_custom_manifest_builder(tmp_project_dir):
    child = pexpect.spawn(
        f"ethpm create --manifest-wizard --project-dir {tmp_project_dir}"
    )
    child.expect(f"ethPM CLI v{ETHPM_CLI_VERSION}\r\n")
    child.expect("\r\n")
    child.expect("Manifest Creator\r\n")
    child.expect("----------------\r\n")
    child.expect("Create ethPM manifests for local projects.")
    child.expect("Project directory must include solc output.")
    child.expect("Follow the steps in the docs to generate solc output.")
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
    child.expect("PackageRegistry\r\n")
    child.expect("PackageRegistryInterface. \r\n")
    child.expect("Would you like to include all available contract types?")
    child.sendline("y")
    child.expect("3 sources available.\r\n")
    child.expect("\r\n")
    child.expect("Ownable.sol\r\n")
    child.expect("PackageRegistry.sol\r\n")
    child.expect("PackageRegistryInterface.sol. \r\n")
    child.expect("Would you like to include all available sources?")
    child.sendline("y")
    child.expect("Would you like to automatically inline all sources?")
    child.sendline("y")
    child.expect("Would you like to validate your manifest against the json schema?")
    child.sendline("y")
    child.expect(
        f"Manifest successfully created and written to {tmp_project_dir}/2.0.0a1.json"
    )
    assert filecmp.cmp(
        ASSETS_DIR / "registry" / "2.0.0a1.json", tmp_project_dir / "2.0.0a1.json"
    )


def test_basic_manifest_builder(tmp_project_dir):
    child = pexpect.spawn(
        f"ethpm create --basic-manifest --project-dir {tmp_project_dir} "
        "--package-name wallet --package-version 1.0.0"
    )
    child.expect(f"ethPM CLI v{ETHPM_CLI_VERSION}\r\n")
    child.expect("\r\n")
    child.expect(
        f"Manifest successfully created and written to {tmp_project_dir}/1.0.0.json"
    )


def test_create_solc_input(tmp_project_dir):
    child = pexpect.spawn(f"ethpm create --solc-input --project-dir {tmp_project_dir}")
    child.expect(f"ethPM CLI v{ETHPM_CLI_VERSION}\r\n")
    child.expect("\r\n")
    child.expect(
        "Solidity compiler input successfully created and "
        f"written to {tmp_project_dir}/{SOLC_INPUT}"
    )
