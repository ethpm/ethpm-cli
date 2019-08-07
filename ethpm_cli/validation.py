from argparse import Namespace
import json
import os
from pathlib import Path

from eth_typing import URI
from ethpm.backends.registry import is_valid_registry_uri
from ethpm.exceptions import EthPMValidationError
from ethpm.uri import is_ipfs_uri, is_valid_content_addressed_github_uri
from ethpm.validation.package import validate_package_name
from web3 import Web3

from ethpm_cli._utils.etherscan import is_etherscan_uri
from ethpm_cli.constants import ETHERSCAN_KEY_ENV_VAR, SOLC_OUTPUT
from ethpm_cli.exceptions import (
    EtherscanKeyNotFound,
    InstallError,
    UriNotSupportedError,
    ValidationError,
)


def validate_parent_directory(parent_dir: Path, child_dir: Path) -> None:
    if parent_dir not in child_dir.parents:
        raise InstallError(f"{parent_dir} was not found in {child_dir} directory tree.")


def validate_project_directory(project_dir: Path) -> None:
    if not project_dir.is_dir():
        raise ValidationError(f"{project_dir} is not a valid directory")

    if not (project_dir / "contracts").is_dir():
        raise ValidationError(
            f"{project_dir} must contain a contracts/ directory that contains project contracts."
        )


def validate_solc_output(project_dir: Path) -> None:
    solc_output_path = project_dir / SOLC_OUTPUT
    if not solc_output_path.is_file():
        raise ValidationError(
            f"{project_dir} does not contain solc output. Please follow the steps in the "
            "documentation to generate your Solidity compiler output."
        )
    try:
        solc_output_data = json.loads(solc_output_path.read_text())
    except ValueError:
        raise ValidationError(
            f"Content found at {solc_output_path} does not look like valid json."
        )

    if "contracts" not in solc_output_data:
        raise ValidationError(
            f"JSON found at {solc_output_path} does not look like valid "
            "Solidity compiler standard json output."
        )


def validate_install_cli_args(args: Namespace) -> None:
    validate_supported_uri(args.uri)
    if args.alias:
        validate_alias(args.alias)

    if args.ethpm_dir:
        validate_ethpm_dir(args.ethpm_dir)

    if is_etherscan_uri(args.uri):
        if not args.package_name or not args.package_version:
            raise InstallError(
                "To install an Etherscan verified contract, you must specify both the "
                "--package-name and --package-version."
            )
    else:
        if args.package_name:
            raise InstallError(
                "You cannot redefine the package_name of an existing package. "
                "Consider aliasing the package instead."
            )

        if args.package_version:
            raise InstallError(
                "You cannot redefine the version of an existing package."
            )


def validate_uninstall_cli_args(args: Namespace) -> None:
    validate_package_name(args.package)
    if args.ethpm_dir:
        validate_ethpm_dir(args.ethpm_dir)


def validate_etherscan_key_available() -> None:
    if ETHERSCAN_KEY_ENV_VAR not in os.environ:
        raise EtherscanKeyNotFound(
            "No Etherscan API key found. Please ensure that the "
            f"{ETHERSCAN_KEY_ENV_VAR} environment variable is set."
        )


def validate_supported_uri(uri: URI) -> None:
    if (
        not is_ipfs_uri(uri)
        and not is_etherscan_uri(uri)  # noqa: W503
        and not is_valid_registry_uri(uri)  # noqa: W503
        and not is_valid_content_addressed_github_uri(uri)  # noqa: W503
    ):
        raise UriNotSupportedError(
            f"Target uri: {uri} not a currently supported uri. "
            "Target uris must be one of: ipfs, github blob, etherscan, or registry."
        )


def validate_alias(alias: str) -> None:
    try:
        validate_package_name(alias)
    except EthPMValidationError:
        raise ValidationError(
            f"{alias} is not a valid package name. All aliases must conform "
            "to the ethpm spec definition of a package name."
        )


def validate_ethpm_dir(ethpm_dir: Path) -> None:
    if ethpm_dir.name != "_ethpm_packages" or not ethpm_dir.is_dir():
        raise InstallError(
            "--ethpm-dir must point to an existing '_ethpm_packages' directory."
        )


def validate_chain_data_store(chain_data_path: Path, w3: Web3) -> None:
    """
    Validates that chain_data_path points to a file corresponding
    to the provided web3 instance.
    """
    if not chain_data_path.is_file():
        raise InstallError(
            f"{chain_data_path} does not appear to be a valid EthPM CLI datastore."
        )

    chain_data = json.loads(chain_data_path.read_text())
    if chain_data["chain_id"] != w3.eth.chainId:
        raise InstallError(
            f"Chain ID found in EthPM CLI datastore: {chain_data['chain_id']} "
            f"does not match chain ID of provided web3 instance: {w3.eth.chainId}"
        )
