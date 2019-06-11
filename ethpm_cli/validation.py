from argparse import Namespace
import json
from pathlib import Path
import os

from eth_typing import URI
from eth_utils import is_hex_address
from ethpm.backends.registry import is_valid_registry_uri
from ethpm.exceptions import EthPMValidationError
from ethpm.uri import is_supported_content_addressed_uri
from ethpm.validation.package import validate_package_name
from web3 import Web3

from ethpm_cli.constants import SOLC_OUTPUT
from ethpm_cli.exceptions import InstallError, UriNotSupportedError, ValidationError


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
    if args.uri:
        validate_target_uri(args.uri)

    if args.alias:
        validate_alias(args.alias)

    if args.ethpm_dir:
        validate_ethpm_dir(args.ethpm_dir)

    # test
    if args.etherscan:
        validate_address(args.etherscan)

        if "package_name" not in args:
            raise InstallError

        if "version" not in args:
            raise InstallError


def validate_uninstall_cli_args(args: Namespace) -> None:
    validate_package_name(args.package)
    if args.ethpm_dir:
        validate_ethpm_dir(args.ethpm_dir)


def validate_verify_cli_args(args: Namespace, config) -> None:
    validate_address(args.address)
    # contract type name / id needs cleaning up
    validate_package_is_installed(args.contract_type, config)


def validate_package_is_installed(contract_type_id, config):
    package, contract_type = contract_type_id.split(":")
    validate_package_name(package)
    # dupe code from ethpm_cli.install
    if not os.path.exists(config.ethpm_dir / package):
        raise InstallError(f"{package} is not installed.")


def validate_address(address):
    if not is_hex_address(address):
        raise ValidationError(f"{address} is not a valid hex address.")


def validate_target_uri(uri: URI) -> None:
    if not is_supported_content_addressed_uri(uri) and not is_valid_registry_uri(uri):
        raise UriNotSupportedError(
            f"Target uri: {uri} not a currently supported uri. "
            "Target uris must be one of: ipfs, github blob, or registry."
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
