from argparse import Namespace
import json
from pathlib import Path

from eth_typing import URI
from ethpm.backends.registry import is_valid_registry_uri
from ethpm.exceptions import ValidationError as EthPMValidationError
from ethpm.uri import is_supported_content_addressed_uri
from ethpm.validation.package import validate_package_name
from web3 import Web3

from ethpm_cli.exceptions import InstallError, UriNotSupportedError, ValidationError


def validate_parent_directory(parent_dir: Path, child_dir: Path) -> None:
    if parent_dir not in child_dir.parents:
        raise InstallError(f"{parent_dir} was not found in {child_dir} directory tree.")


def validate_install_cli_args(args: Namespace) -> None:
    validate_target_uri(args.uri)
    if args.alias:
        validate_alias(args.alias)

    if args.ethpm_dir:
        validate_ethpm_dir(args.ethpm_dir)


def validate_uninstall_cli_args(args: Namespace) -> None:
    validate_package_name(args.package)
    if args.ethpm_dir:
        validate_ethpm_dir(args.ethpm_dir)


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
            f"--ethpm-dir must point to an existing '_ethpm_packages' directory."
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
