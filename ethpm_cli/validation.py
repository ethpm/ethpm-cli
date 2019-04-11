from argparse import Namespace

from ethpm.typing import URI
from ethpm.utils.ipfs import is_ipfs_uri
from ethpm.utils.uri import is_valid_content_addressed_github_uri
from ethpm.validation import is_valid_registry_uri, validate_package_name

from ethpm_cli.exceptions import InstallError, UriNotSupportedError, ValidationError


def validate_cli_args(args: Namespace) -> None:
    validate_supported_target_uri(args.uri)

    if args.alias:
        try:
            validate_package_name(args.alias)
        except Exception:
            raise ValidationError(
                f"{args.alias} is not a valid package name. All aliases must conform "
                "to the ethpm spec definition of a package name."
            )

    if args.local_ipfs:
        assert type(args.local_ipfs) is bool

    if args.packages_dir:
        if args.packages_dir.name != "ethpm_packages" or not args.packages_dir.is_dir():
            raise InstallError(
                f"--packages-dir must point to an existing 'ethpm_packages' directory."
            )


def validate_supported_target_uri(uri: URI) -> None:
    if (
        not is_ipfs_uri(uri)
        and not is_valid_registry_uri(uri)  # noqa: W503
        and not is_valid_content_addressed_github_uri(uri)  # noqa: W503
    ):
        raise UriNotSupportedError(
            f"Target uri: {uri} not a currently supported uri. "
            "Target uris must be one of: ipfs, github blob, or registry."
        )
