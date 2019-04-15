from argparse import Namespace
from pathlib import Path

from ethpm.typing import URI
from ethpm.utils.ipfs import is_ipfs_uri
from ethpm.utils.uri import is_valid_content_addressed_github_uri
from ethpm.validation import is_valid_registry_uri, validate_package_name

from ethpm_cli.exceptions import InstallError, UriNotSupportedError, ValidationError


def validate_parent_directory(parent_dir: Path, child_dir: Path) -> None:
    if parent_dir not in child_dir.parents:
        raise InstallError(f"{parent_dir} was not found in {child_dir} directory tree.")


def validate_cli_args(args: Namespace) -> None:
    validate_target_uri(args.uri)
    validate_alias(args.alias)
    validate_ethpm_dir(args.packages_dir)


def validate_target_uri(uri: URI) -> None:
    if (
        not is_ipfs_uri(uri)
        and not is_valid_registry_uri(uri)  # noqa: W503
        and not is_valid_content_addressed_github_uri(uri)  # noqa: W503
    ):
        raise UriNotSupportedError(
            f"Target uri: {uri} not a currently supported uri. "
            "Target uris must be one of: ipfs, github blob, or registry."
        )


def validate_alias(alias: str) -> None:
    if alias:
        try:
            validate_package_name(alias)
        except Exception:
            raise ValidationError(
                f"{alias} is not a valid package name. All aliases must conform "
                "to the ethpm spec definition of a package name."
            )


def validate_ethpm_dir(ethpm_dir: Path) -> None:
    if ethpm_dir:
        if ethpm_dir.name != "ethpm_packages" or not ethpm_dir.is_dir():
            raise InstallError(
                f"--packages-dir must point to an existing 'ethpm_packages' directory."
            )
